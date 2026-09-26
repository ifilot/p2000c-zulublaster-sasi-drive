#include "core/terminal.h"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace p2000c {

Terminal::Terminal() { reset(); }

void Terminal::reset() {
  screen_.fill(0x20);
  attributes_.fill(kDefaultAttribute);
  graphic_screen_.fill(0);
  input_.clear();
  graphic_parameters_.clear();
  escape_state_ = EscapeState::kNone;
  cursor_column_ = 0;
  cursor_row_ = 0;
  pending_row_ = 0;
  skip_bytes_ = 0;
  graphic_parameter_count_ = 0;
  graphic_data_count_ = 0;
  graphic_data_address_ = 0;
  graphic_cursor_x_ = 0;
  graphic_cursor_y_ = 0;
  graphic_origin_x_ = 0;
  graphic_origin_y_ = 0;
  handshake_echoes_ = 0;
  graphic_command_ = 0;
  attribute_ = kDefaultAttribute;
  graphics_mode_ = GraphicsMode::kCharacter;
  keyboard_locked_ = false;
  cursor_visible_ = true;
  ++revision_;
}

void Terminal::begin_handshake() {
  input_.push_back(0x55);
  handshake_echoes_ = 2;
}

void Terminal::receive(std::uint8_t value) {
  if (trace_ != nullptr) {
    trace_->put(static_cast<char>(value));
  }
  if (handshake_echoes_ > 0) {
    --handshake_echoes_;
    if (handshake_echoes_ == 1) {
      input_.push_back(0xaa);
    }
    return;
  }

  switch (escape_state_) {
    case EscapeState::kCommand:
      escape_command(value);
      return;
    case EscapeState::kCursorRow:
      pending_row_ =
          std::clamp(static_cast<int>(value) - 0x20, 0, active_rows() - 1);
      escape_state_ = EscapeState::kCursorColumn;
      return;
    case EscapeState::kCursorColumn:
      cursor_row_ = pending_row_;
      cursor_column_ =
          std::clamp(static_cast<int>(value) - 0x20, 0,
                     active_columns() - 1);
      escape_state_ = EscapeState::kNone;
      return;
    case EscapeState::kAttribute:
      attribute_ = value;
      escape_state_ = EscapeState::kNone;
      return;
    case EscapeState::kLockLines:
      escape_state_ = EscapeState::kNone;
      return;
    case EscapeState::kSkipBytes:
      if (--skip_bytes_ == 0) {
        escape_state_ = EscapeState::kNone;
      }
      return;
    case EscapeState::kGraphicParameters:
      graphic_parameters_.push_back(value);
      if (static_cast<int>(graphic_parameters_.size()) ==
          graphic_parameter_count_) {
        execute_graphic_command();
      }
      return;
    case EscapeState::kGraphicData:
      graphic_screen_[graphic_data_address_] = value;
      graphic_data_address_ = next_graphic_address(graphic_data_address_);
      if (--graphic_data_count_ == 0) {
        escape_state_ = EscapeState::kNone;
      }
      return;
    case EscapeState::kNone:
      break;
  }

  switch (value) {
    case 0x01:
      cursor_column_ = 0;
      cursor_row_ = 0;
      break;
    case 0x02:
      keyboard_locked_ = false;
      break;
    case 0x04:
      cursor_column_ = active_columns() - 1;
      cursor_row_ = active_rows() - 1;
      break;
    case 0x06:
      if (++cursor_column_ == active_columns()) {
        cursor_column_ = 0;
        cursor_down();
      }
      break;
    case 0x07:
      ++bell_revision_;
      break;
    case 0x08:
    case 0x15:
      cursor_column_ = std::max(cursor_column_ - 1, 0);
      break;
    case 0x09:
      cursor_column_ =
          std::min((cursor_column_ + 8) & ~7, active_columns() - 1);
      break;
    case 0x0a:
      cursor_down();
      break;
    case 0x0c:
      screen_.fill(0x20);
      attributes_.fill(attribute_);
      cursor_column_ = 0;
      cursor_row_ = 0;
      ++revision_;
      break;
    case 0x0d:
      cursor_column_ = 0;
      break;
    case 0x18:
      reset();
      break;
    case 0x19:
      keyboard_locked_ = true;
      break;
    case 0x1a:
      cursor_row_ = std::max(cursor_row_ - 1, 0);
      break;
    case 0x1b:
      escape_state_ = EscapeState::kCommand;
      break;
    default:
      if (value >= 0x20 && value != 0x7f) {
        put_character(value);
      }
      break;
  }
}

void Terminal::queue_key(std::uint8_t value) {
  if (!keyboard_locked_) {
    input_.push_back(value);
  }
}

std::uint8_t Terminal::take_input() {
  if (input_.empty()) {
    return 0;
  }
  const std::uint8_t value = input_.front();
  input_.pop_front();
  return value;
}

void Terminal::put_character(std::uint8_t value) {
  const int columns = active_columns();
  const std::size_t position = cursor_row_ * columns + cursor_column_;
  screen_[position] = value;
  attributes_[position] = attribute_;
  ++revision_;
  if (++cursor_column_ == columns) {
    cursor_column_ = 0;
    cursor_down();
  }
}

void Terminal::cursor_down() {
  if (++cursor_row_ == active_rows()) {
    cursor_row_ = active_rows() - 1;
    scroll_up();
  }
}

void Terminal::scroll_up() {
  const int columns = active_columns();
  const int cells = columns * active_rows();
  std::move(screen_.begin() + columns, screen_.begin() + cells,
            screen_.begin());
  std::fill(screen_.begin() + cells - columns, screen_.begin() + cells, 0x20);
  std::move(attributes_.begin() + columns, attributes_.begin() + cells,
            attributes_.begin());
  std::fill(attributes_.begin() + cells - columns,
            attributes_.begin() + cells, attribute_);
  ++revision_;
}

void Terminal::scroll_down() {
  const int columns = active_columns();
  const int cells = columns * active_rows();
  std::move_backward(screen_.begin(), screen_.begin() + cells - columns,
                     screen_.begin() + cells);
  std::fill(screen_.begin(), screen_.begin() + columns, 0x20);
  std::move_backward(attributes_.begin(),
                     attributes_.begin() + cells - columns,
                     attributes_.begin() + cells);
  std::fill(attributes_.begin(), attributes_.begin() + columns, attribute_);
  ++revision_;
}

void Terminal::escape_command(std::uint8_t value) {
  escape_state_ = EscapeState::kNone;
  switch (value) {
    case 'p':
      // Philips CP/M Reference 10-5: this enters the Intel HEX loader,
      // not VT52 inverse video. Fail visibly until the loader is modeled.
      throw std::runtime_error("Unsupported P2000C ESC p: terminal program loader requested");
    case 'Y':
      escape_state_ = EscapeState::kCursorRow;
      break;
    case 'K': {
      const int columns = active_columns();
      const auto begin =
          screen_.begin() + cursor_row_ * columns + cursor_column_;
      const auto end = screen_.begin() + (cursor_row_ + 1) * columns;
      std::fill(begin, end, 0x20);
    }
      ++revision_;
      break;
    case 'k': {
      const int cells = active_columns() * active_rows();
      const auto begin =
          screen_.begin() + cursor_row_ * active_columns() + cursor_column_;
      std::fill(begin, screen_.begin() + cells, 0x20);
    }
      ++revision_;
      break;
    case 'S':
      scroll_up();
      break;
    case 'T':
      scroll_down();
      break;
    case 'C':
      cursor_visible_ = true;
      ++revision_;
      break;
    case 'c':
      cursor_visible_ = false;
      ++revision_;
      break;
    case '0':
      escape_state_ = EscapeState::kAttribute;
      break;
    case '5':
      set_graphics_mode(GraphicsMode::kMedium256);
      break;
    case '3':
      set_graphics_mode(GraphicsMode::kHigh512);
      break;
    case '4':
      set_graphics_mode(GraphicsMode::kCharacter);
      break;
    case 'd':
    case 'D':
    case 'm':
    case 'M':
    case 'v':
    case 'z':
      if (graphics_mode_ != GraphicsMode::kCharacter) {
        begin_graphic_command(value,
                              graphics_mode_ == GraphicsMode::kHigh512 ? 3 : 2);
      }
      break;
    case 'y':
    case 'U':
    case 'w':
    case 'F':
    case 'f':
      if (graphics_mode_ != GraphicsMode::kCharacter) {
        begin_graphic_command(value, 4);
      }
      break;
    case 'r':
    case 't':
      if (graphics_mode_ != GraphicsMode::kCharacter) {
        begin_graphic_command(
            value, (graphics_mode_ == GraphicsMode::kHigh512 ? 3 : 2) + 2);
      }
      break;
    case 'A':
      escape_state_ = EscapeState::kLockLines;
      break;
    case '@':
      skip_bytes_ = 360;
      escape_state_ = EscapeState::kSkipBytes;
      break;
    case '!':
      skip_bytes_ = 256;
      escape_state_ = EscapeState::kSkipBytes;
      break;
    case '+':
      skip_bytes_ = 2;
      escape_state_ = EscapeState::kSkipBytes;
      break;
    case '?':
      queue_status();
      break;
    default:
      break;
  }
}

void Terminal::queue_status() {
  const int columns = active_columns();
  input_.push_back(static_cast<std::uint8_t>(cursor_column_ + 1));
  input_.push_back(static_cast<std::uint8_t>(cursor_row_ + 1));
  input_.push_back(screen_[cursor_row_ * columns + cursor_column_]);
  std::uint8_t status = keyboard_locked_ ? 0x20 : 0x00;
  if (graphics_mode_ != GraphicsMode::kCharacter) {
    status |= 0x01;
  }
  if (graphics_mode_ == GraphicsMode::kHigh512) {
    status |= 0x02;
  }
  input_.push_back(status);
  input_.push_back(static_cast<std::uint8_t>(graphic_cursor_x_));
  input_.push_back(static_cast<std::uint8_t>(graphic_cursor_x_ >> 8));
  input_.push_back(static_cast<std::uint8_t>(graphic_cursor_y_));
  input_.insert(input_.end(), 5, 0x00);
}

void Terminal::set_graphics_mode(GraphicsMode mode) {
  if (mode == GraphicsMode::kCharacter) {
    screen_.fill(0x20);
    attributes_.fill(kDefaultAttribute);
    cursor_column_ = 0;
    cursor_row_ = 0;
  } else if (graphics_mode_ == GraphicsMode::kCharacter) {
    const int linear_cursor = cursor_row_ * kColumns + cursor_column_;
    cursor_row_ = std::min(linear_cursor / 64, 20);
    cursor_column_ = linear_cursor % 64;
  }
  graphics_mode_ = mode;
  graphic_screen_.fill(0);
  graphic_cursor_x_ = 0;
  graphic_cursor_y_ = 0;
  graphic_origin_x_ = 0;
  graphic_origin_y_ = 0;
  ++revision_;
}

void Terminal::begin_graphic_command(std::uint8_t command,
                                     int parameter_count) {
  graphic_command_ = command;
  graphic_parameter_count_ = parameter_count;
  graphic_parameters_.clear();
  escape_state_ = EscapeState::kGraphicParameters;
}

std::pair<int, int> Terminal::graphic_coordinate(std::size_t offset) const {
  if (graphics_mode_ == GraphicsMode::kHigh512) {
    const int x = graphic_parameters_[offset] |
                  (static_cast<int>(graphic_parameters_[offset + 1]) << 8);
    return {x, graphic_parameters_[offset + 2]};
  }
  return {graphic_parameters_[offset], graphic_parameters_[offset + 1]};
}

std::size_t Terminal::graphic_byte_address(int x, int y) const {
  const int pixels_per_byte =
      graphics_mode_ == GraphicsMode::kHigh512 ? 8 : 4;
  const int row = std::clamp(kGraphicHeight - 1 - y, 0, kGraphicHeight - 1);
  const int byte_column = std::clamp(x / pixels_per_byte, 0,
                                     kGraphicBytesPerLine - 1);
  return static_cast<std::size_t>(row * kGraphicBytesPerLine + byte_column);
}

void Terminal::set_graphic_pixel(int x, int y, bool set) {
  const int width =
      graphics_mode_ == GraphicsMode::kHigh512 ? kGraphicWidth : 256;
  if (x < 0 || x >= width || y < 0 || y >= kGraphicHeight) {
    return;
  }
  const std::size_t address = graphic_byte_address(x, y);
  if (graphics_mode_ == GraphicsMode::kHigh512) {
    const std::uint8_t mask = static_cast<std::uint8_t>(0x80 >> (x & 7));
    if (set) {
      graphic_screen_[address] |= mask;
    } else {
      graphic_screen_[address] &= static_cast<std::uint8_t>(~mask);
    }
  } else {
    const int pixel = x & 3;
    const std::uint8_t mask = static_cast<std::uint8_t>(
        (0x80 >> pixel) | (0x08 >> pixel));
    graphic_screen_[address] &= static_cast<std::uint8_t>(~mask);
    if (set) {
      // Medium graphics stores brightness as two parallel bit planes.
      // Translate serial quarter/bold/normal/half values 00/01/10/11 to
      // graphics-RAM background/bold/normal/half pairs 00/11/10/01.
      const int intensity =
          ((attribute_ & kAttributeIntensityHigh) != 0 ? 2 : 0) |
          ((attribute_ & kAttributeIntensityLow) != 0 ? 1 : 0);
      constexpr std::array<std::uint8_t, 4> kPlaneBits = {
          0x00, 0x03, 0x02, 0x01,
      };
      std::uint8_t bits = 0;
      if ((kPlaneBits[intensity] & 0x02) != 0) {
        bits |= static_cast<std::uint8_t>(0x80 >> pixel);
      }
      if ((kPlaneBits[intensity] & 0x01) != 0) {
        bits |= static_cast<std::uint8_t>(0x08 >> pixel);
      }
      graphic_screen_[address] |= bits;
    }
  }
  ++revision_;
}

// Verified on hardware: the terminal's picture RAM runs bottom-up, so the
// bytes of an ESC r/t transfer fill a line left to right and then continue
// on the line ABOVE it (wrapping from the top line to the bottom one). The
// buffer here is kept top-down for display, hence the row decrement.
std::size_t Terminal::next_graphic_address(std::size_t address) const {
  const std::size_t row = address / kGraphicBytesPerLine;
  const std::size_t column = address % kGraphicBytesPerLine + 1;
  if (column < kGraphicBytesPerLine) {
    return row * kGraphicBytesPerLine + column;
  }
  const std::size_t next_row = row == 0 ? kGraphicHeight - 1 : row - 1;
  return next_row * kGraphicBytesPerLine;
}

void Terminal::draw_graphic_line(int x0, int y0, int x1, int y1, bool set) {
  const int dx = std::abs(x1 - x0);
  const int sx = x0 < x1 ? 1 : -1;
  const int dy = -std::abs(y1 - y0);
  const int sy = y0 < y1 ? 1 : -1;
  int error = dx + dy;
  while (true) {
    set_graphic_pixel(x0, y0, set);
    if (x0 == x1 && y0 == y1) {
      break;
    }
    const int twice_error = 2 * error;
    if (twice_error >= dy) {
      error += dy;
      x0 += sx;
    }
    if (twice_error <= dx) {
      error += dx;
      y0 += sy;
    }
  }
}

void Terminal::execute_graphic_command() {
  escape_state_ = EscapeState::kNone;
  if (graphic_command_ == 'r' || graphic_command_ == 't') {
    const auto [x, y] = graphic_coordinate();
    const std::size_t count_offset =
        graphics_mode_ == GraphicsMode::kHigh512 ? 3 : 2;
    // Verified on hardware: the terminal firmware mishandles a picture
    // transfer whose byte count has a zero low byte (1000 bytes work, 1024
    // and 16128 do not); the data then arrives as ordinary text. Model that
    // as a zero-length transfer so programs hit the same failure here.
    const int count =
        graphic_parameters_[count_offset] == 0
            ? 0
            : graphic_parameters_[count_offset] |
                  (static_cast<int>(graphic_parameters_[count_offset + 1])
                   << 8);
    std::size_t address = graphic_byte_address(x, y);
    if (graphic_command_ == 'r') {
      graphic_data_address_ = address;
      graphic_data_count_ = count;
      if (graphic_data_count_ > 0) {
        escape_state_ = EscapeState::kGraphicData;
      }
    } else {
      for (int index = 0; index < count; ++index) {
        input_.push_back(graphic_screen_[address]);
        address = next_graphic_address(address);
      }
    }
    return;
  }

  if (graphic_command_ == 'y' || graphic_command_ == 'U' ||
      graphic_command_ == 'w' || graphic_command_ == 'F' ||
      graphic_command_ == 'f') {
    const int angle = graphic_parameters_[0] |
                      (static_cast<int>(graphic_parameters_[1]) << 8);
    const int radius = graphic_parameters_[2] |
                       (static_cast<int>(graphic_parameters_[3]) << 8);
    const double radians =
        static_cast<double>(angle) * std::numbers::pi / 180.0;
    const int x = graphic_origin_x_ +
                  static_cast<int>(std::lround(radius * std::cos(radians)));
    const int y = graphic_origin_y_ +
                  static_cast<int>(std::lround(radius * std::sin(radians)));
    if (graphic_command_ == 'y') {
      graphic_cursor_x_ = x;
      graphic_cursor_y_ = y;
    } else if (graphic_command_ == 'F' || graphic_command_ == 'f') {
      set_graphic_pixel(x, y, graphic_command_ == 'F');
    } else {
      draw_graphic_line(graphic_cursor_x_, graphic_cursor_y_, x, y,
                        graphic_command_ == 'U');
      graphic_cursor_x_ = x;
      graphic_cursor_y_ = y;
    }
    return;
  }

  const auto [x, y] = graphic_coordinate();
  switch (graphic_command_) {
    case 'D':
    case 'd':
      set_graphic_pixel(x, y, graphic_command_ == 'D');
      break;
    case 'm':
      graphic_cursor_x_ = x;
      graphic_cursor_y_ = y;
      break;
    case 'M':
    case 'v':
      draw_graphic_line(graphic_cursor_x_, graphic_cursor_y_, x, y,
                        graphic_command_ == 'M');
      graphic_cursor_x_ = x;
      graphic_cursor_y_ = y;
      break;
    case 'z':
      graphic_origin_x_ = x;
      graphic_origin_y_ = y;
      break;
    default:
      break;
  }
}

int Terminal::active_columns() const {
  return graphics_mode_ == GraphicsMode::kCharacter ? kColumns : 64;
}

int Terminal::active_rows() const {
  return graphics_mode_ == GraphicsMode::kCharacter ? kRows : 21;
}

}  // namespace p2000c

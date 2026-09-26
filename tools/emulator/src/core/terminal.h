#ifndef P2000C_CORE_TERMINAL_H_
#define P2000C_CORE_TERMINAL_H_

#include <array>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <ostream>
#include <utility>
#include <vector>

namespace p2000c {

/** Functional replacement for the serial P2000C terminal board. */
class Terminal {
  private:
    static constexpr int kColumns = 80;
    static constexpr int kRows = 24;

    enum class EscapeState {
      kNone,
      kCommand,
      kCursorRow,
      kCursorColumn,
      kAttribute,
      kLockLines,
      kSkipBytes,
      kGraphicParameters,
      kGraphicData,
    };

  public:
    using Screen = std::array<std::uint8_t, kColumns * kRows>;
    using AttributeScreen = std::array<std::uint8_t, kColumns * kRows>;
    static constexpr int kGraphicWidth = 512;
    static constexpr int kGraphicHeight = 252;
    static constexpr int kGraphicBytesPerLine = kGraphicWidth / 8;
    using GraphicScreen =
        std::array<std::uint8_t, kGraphicBytesPerLine * kGraphicHeight>;

    /** Video modes selected by the terminal firmware's ESC 3/4/5 commands. */
    enum class GraphicsMode {
      kCharacter,
      kMedium256,
      kHigh512,
    };

    // ESC 0 attribute-byte layout documented in the terminal firmware manual.
    static constexpr std::uint8_t kAttributeIntensityHigh = 0x40;
    static constexpr std::uint8_t kAttributeUnderline = 0x20;
    static constexpr std::uint8_t kAttributeInverse = 0x10;
    static constexpr std::uint8_t kAttributeBlink = 0x02;
    static constexpr std::uint8_t kAttributeIntensityLow = 0x01;
    static constexpr std::uint8_t kDefaultAttribute = kAttributeIntensityHigh;

    /** Creates a reset 80x24 terminal. */
    Terminal();

    /** Clears terminal state, queues, and screen contents. */
    void reset();

    /** Queues the two bytes expected by the mainboard IPL handshake. */
    void begin_handshake();

    /** Accepts a serial byte transmitted by the mainboard. */
    void receive(std::uint8_t value);

    /** Copies every received byte to a trace stream (nullptr disables). */
    void set_trace(std::ostream* trace) { trace_ = trace; }

    /** Queues a translated keyboard byte for the mainboard receiver. */
    void queue_key(std::uint8_t value);

    /** Returns whether a byte is waiting for the mainboard. */
    bool has_input() const { return !input_.empty(); }

    /** Removes and returns the next byte for the mainboard. */
    std::uint8_t take_input();

    /** Returns the current 80x24 character buffer. */
    const Screen& screen() const { return screen_; }

    /** Returns the terminal attribute byte stored for every character cell. */
    const AttributeScreen& attributes() const { return attributes_; }

    /** Returns the currently selected character or graphics mode. */
    GraphicsMode graphics_mode() const { return graphics_mode_; }

    /** Returns the terminal board's 16,128-byte visible graphics RAM. */
    const GraphicScreen& graphic_screen() const { return graphic_screen_; }

    /** Returns a counter changed after every visible screen update. */
    std::uint64_t revision() const { return revision_; }

    /** Returns a counter incremented whenever BEL activates the beeper. */
    std::uint64_t bell_revision() const { return bell_revision_; }

    /** Returns the zero-based cursor column. */
    int cursor_column() const { return cursor_column_; }

    /** Returns the zero-based cursor row. */
    int cursor_row() const { return cursor_row_; }

    /** Returns whether the terminal firmware has enabled the cursor. */
    bool cursor_visible() const { return cursor_visible_; }

  private:
    /** Places a printable character at the cursor and advances it. */
    void put_character(std::uint8_t value);

    /** Moves down, scrolling at the bottom of the display. */
    void cursor_down();

    /** Scrolls the complete display upward by one row. */
    void scroll_up();

    /** Scrolls the complete display downward by one row. */
    void scroll_down();

    /** Interprets the byte following ESC. */
    void escape_command(std::uint8_t value);

    /** Queues the documented 12-byte terminal status reply. */
    void queue_status();

    /** Selects a graphics mode, or clears both planes on return to text. */
    void set_graphics_mode(GraphicsMode mode);

    /** Begins collecting parameters for a graphics escape command. */
    void begin_graphic_command(std::uint8_t command, int parameter_count);

    /** Executes a graphics command after all of its parameters arrive. */
    void execute_graphic_command();

    /** Reads a Cartesian coordinate from the collected command bytes. */
    std::pair<int, int> graphic_coordinate(std::size_t offset = 0) const;

    /** Converts a bottom-left coordinate to graphics-RAM byte position. */
    std::size_t graphic_byte_address(int x, int y) const;

    /** Next byte of a picture transfer: along the line, then the line above. */
    std::size_t next_graphic_address(std::size_t address) const;

    /** Sets or clears one logical graphics pixel at the current intensity. */
    void set_graphic_pixel(int x, int y, bool set);

    /** Draws or clears a clipped Cartesian line. */
    void draw_graphic_line(int x0, int y0, int x1, int y1, bool set);

    /** Returns the current logical width (80 text, 64 mixed graphics). */
    int active_columns() const;

    /** Returns the current logical height (24 text, 21 mixed graphics). */
    int active_rows() const;

    Screen screen_{};
    AttributeScreen attributes_{};
    GraphicScreen graphic_screen_{};
    std::deque<std::uint8_t> input_;
    std::vector<std::uint8_t> graphic_parameters_;
    EscapeState escape_state_ = EscapeState::kNone;
    int cursor_column_ = 0;
    int cursor_row_ = 0;
    int pending_row_ = 0;
    int skip_bytes_ = 0;
    int graphic_parameter_count_ = 0;
    int graphic_data_count_ = 0;
    std::size_t graphic_data_address_ = 0;
    int graphic_cursor_x_ = 0;
    int graphic_cursor_y_ = 0;
    int graphic_origin_x_ = 0;
    int graphic_origin_y_ = 0;
    int handshake_echoes_ = 0;
    std::uint8_t graphic_command_ = 0;
    std::uint8_t attribute_ = kDefaultAttribute;
    GraphicsMode graphics_mode_ = GraphicsMode::kCharacter;
    bool keyboard_locked_ = false;
    bool cursor_visible_ = true;
    std::uint64_t revision_ = 0;
    std::uint64_t bell_revision_ = 0;
    std::ostream* trace_ = nullptr;
};

}  // namespace p2000c

#endif  // P2000C_CORE_TERMINAL_H_

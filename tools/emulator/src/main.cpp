#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "core/p2000c_machine.h"

namespace {

constexpr std::uint64_t kDefaultWaitCycles = 200'000'000;
constexpr std::uint64_t kDefaultChunkCycles = 100'000;

enum class ActionKind {
  kSend,
  kWaitFor,
  kRun,
  kSwapFloppyA,
  kSwapFloppyB,
};

struct Action {
  ActionKind kind = ActionKind::kRun;
  std::string text;
  std::uint64_t cycles = 0;
};

struct MemoryDump {
  std::uint16_t address = 0;
  std::size_t length = 0;
};

struct Options {
  std::optional<std::filesystem::path> ipl;
  std::array<std::optional<std::filesystem::path>, 2> floppies;
  std::array<std::optional<std::filesystem::path>, 2> hard_disks;
  std::vector<Action> actions;
  std::vector<MemoryDump> memory_dumps;
  std::optional<std::filesystem::path> graphics_dump;
  std::optional<std::filesystem::path> terminal_trace;
  std::uint64_t wait_cycles = kDefaultWaitCycles;
  std::uint64_t chunk_cycles = kDefaultChunkCycles;
  bool write_through = false;
  bool fast_storage = false;
  bool copower = false;
  std::size_t copower_kib = 512;
  bool json = false;
  bool help = false;
};

class TemporaryMedia {
 public:
  TemporaryMedia() = default;
  TemporaryMedia(const TemporaryMedia&) = delete;
  TemporaryMedia& operator=(const TemporaryMedia&) = delete;

  ~TemporaryMedia() {
    if (!directory_.empty()) {
      std::error_code error;
      std::filesystem::remove_all(directory_, error);
    }
  }

  std::filesystem::path copy(const std::filesystem::path& source,
                             std::string_view drive_name) {
    ensure_directory();
    std::filesystem::path destination =
        directory_ / (std::string(drive_name) + source.extension().string());
    std::error_code error;
    std::filesystem::copy_file(source, destination,
                               std::filesystem::copy_options::overwrite_existing,
                               error);
    if (error) {
      throw std::runtime_error("Could not create temporary copy of " +
                               source.string() + ": " + error.message());
    }
    return destination;
  }

 private:
  void ensure_directory() {
    if (!directory_.empty()) {
      return;
    }
    std::error_code temp_error;
    const std::filesystem::path base =
        std::filesystem::temp_directory_path(temp_error);
    if (temp_error) {
      throw std::runtime_error("Could not locate the temporary directory: " +
                               temp_error.message());
    }

    std::random_device random;
    for (int attempt = 0; attempt < 128; ++attempt) {
      const auto tick = std::chrono::steady_clock::now()
                            .time_since_epoch()
                            .count();
      const std::filesystem::path candidate =
          base / ("p2000c-cli-" + std::to_string(tick) + "-" +
                  std::to_string(random()));
      std::error_code create_error;
      if (std::filesystem::create_directory(candidate, create_error)) {
        directory_ = candidate;
        return;
      }
      if (create_error &&
          create_error != std::errc::file_exists) {
        throw std::runtime_error("Could not create a temporary directory: " +
                                 create_error.message());
      }
    }
    throw std::runtime_error("Could not create a unique temporary directory.");
  }

  std::filesystem::path directory_;
};

void print_usage(std::ostream& output) {
  output
      << "Usage: p2000c-mini --ipl FILE [MEDIA] [ACTIONS] [OPTIONS]\n"
      << "\nMedia (copied to temporary writable files by default):\n"
      << "  --floppy-a FILE       Mount a 640 or 800 KiB FLP image in drive A\n"
      << "  --floppy-b FILE       Mount a 640 or 800 KiB FLP image in drive B\n"
      << "  --hard-disk-0 FILE    Mount a 10 MiB HDA image as physical disk 0\n"
      << "  --hard-disk-1 FILE    Mount a 10 MiB HDA image as physical disk 1\n"
      << "  --write-through       Apply guest writes directly to those files\n"
      << "\nActions are performed from left to right:\n"
      << "  --wait-for TEXT       Run until TEXT appears on the 80x24 screen\n"
      << "  --send TEXT           Queue keyboard bytes (supports \\r, \\n, \\t,"
         " \\xNN, \\\\)\n"
      << "  --send-file FILE      Queue every byte from FILE as keyboard input\n"
      << "  --run CYCLES          Run for a fixed number of Z80 T-states\n"
      << "  --swap-floppy-a FILE  Replace drive A media at this action point\n"
      << "  --swap-floppy-b FILE  Replace drive B media at this action point\n"
      << "\nOutput and execution:\n"
      << "  --output text|json    Select screen text (default) or structured JSON\n"
      << "  --dump-memory A:L     Include L bytes starting at address A\n"
      << "  --dump-graphics FILE  Write the 16128-byte graphics RAM to FILE\n"
      << "  --trace-terminal FILE Append every byte sent to the terminal to FILE\n"
      << "  --wait-cycles N       Per-wait timeout (default 200000000)\n"
      << "  --chunk-cycles N      Wait polling interval (default 100000)\n"
      << "  --fast-storage        Bypass emulated floppy latency\n"
      << "  --copower             Install the 512 KiB Philips CoPower board\n"
      << "  --copower-ram KIB     Install a 256 or 512 KiB CoPower board\n"
      << "  --help                Show this help\n"
      << "\nNumbers accept decimal or a 0x hexadecimal prefix. A wait that times out\n"
      << "still emits the final screen and returns exit status 3.\n";
}

std::string require_value(int& index, int argc, char* argv[],
                          std::string_view option) {
  if (++index >= argc) {
    throw std::runtime_error("Missing value after " + std::string(option) + ".");
  }
  return argv[index];
}

std::uint64_t parse_number(const std::string& value,
                           std::string_view description) {
  std::size_t consumed = 0;
  try {
    const std::uint64_t result = std::stoull(value, &consumed, 0);
    if (consumed != value.size()) {
      throw std::invalid_argument("trailing characters");
    }
    return result;
  } catch (const std::exception&) {
    throw std::runtime_error("Invalid " + std::string(description) + ": " +
                             value);
  }
}

int hex_digit(char value) {
  if (value >= '0' && value <= '9') {
    return value - '0';
  }
  if (value >= 'a' && value <= 'f') {
    return value - 'a' + 10;
  }
  if (value >= 'A' && value <= 'F') {
    return value - 'A' + 10;
  }
  return -1;
}

std::string decode_text(const std::string& encoded) {
  std::string decoded;
  decoded.reserve(encoded.size());
  for (std::size_t index = 0; index < encoded.size(); ++index) {
    if (encoded[index] != '\\') {
      decoded.push_back(encoded[index]);
      continue;
    }
    if (++index == encoded.size()) {
      throw std::runtime_error("A text argument ends with an incomplete escape.");
    }
    switch (encoded[index]) {
      case 'r':
        decoded.push_back('\r');
        break;
      case 'n':
        decoded.push_back('\n');
        break;
      case 't':
        decoded.push_back('\t');
        break;
      case '0':
        decoded.push_back('\0');
        break;
      case '\\':
        decoded.push_back('\\');
        break;
      case 'x': {
        if (index + 2 >= encoded.size()) {
          throw std::runtime_error("\\x must be followed by two hex digits.");
        }
        const int high = hex_digit(encoded[index + 1]);
        const int low = hex_digit(encoded[index + 2]);
        if (high < 0 || low < 0) {
          throw std::runtime_error("\\x must be followed by two hex digits.");
        }
        decoded.push_back(static_cast<char>((high << 4) | low));
        index += 2;
        break;
      }
      default:
        throw std::runtime_error("Unsupported text escape: \\" +
                                 std::string(1, encoded[index]));
    }
  }
  return decoded;
}

std::string read_file(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    throw std::runtime_error("Could not open input file: " + path.string());
  }
  return std::string(std::istreambuf_iterator<char>(input),
                     std::istreambuf_iterator<char>());
}

MemoryDump parse_memory_dump(const std::string& value) {
  const std::size_t separator = value.find(':');
  if (separator == std::string::npos) {
    throw std::runtime_error("A memory dump must have the form ADDRESS:LENGTH.");
  }
  const std::uint64_t address =
      parse_number(value.substr(0, separator), "memory address");
  const std::uint64_t length =
      parse_number(value.substr(separator + 1), "memory length");
  if (address > 0xffff || length > 0x10000 || address + length > 0x10000) {
    throw std::runtime_error("Memory dump lies outside the 64 KiB address space.");
  }
  return {static_cast<std::uint16_t>(address),
          static_cast<std::size_t>(length)};
}

Options parse_options(int argc, char* argv[]) {
  Options options;
  for (int index = 1; index < argc; ++index) {
    const std::string argument = argv[index];
    if (argument == "--help" || argument == "-h") {
      options.help = true;
    } else if (argument == "--ipl") {
      options.ipl = require_value(index, argc, argv, argument);
    } else if (argument == "--floppy-a") {
      options.floppies[0] = require_value(index, argc, argv, argument);
    } else if (argument == "--floppy-b") {
      options.floppies[1] = require_value(index, argc, argv, argument);
    } else if (argument == "--hard-disk-0") {
      options.hard_disks[0] = require_value(index, argc, argv, argument);
    } else if (argument == "--hard-disk-1") {
      options.hard_disks[1] = require_value(index, argc, argv, argument);
    } else if (argument == "--write-through") {
      options.write_through = true;
    } else if (argument == "--fast-storage") {
      options.fast_storage = true;
    } else if (argument == "--copower") {
      options.copower = true;
    } else if (argument == "--copower-ram") {
      const auto kib = parse_number(require_value(index, argc, argv, argument), "CoPower RAM");
      if (kib != 256 && kib != 512) {
        throw std::runtime_error("--copower-ram must be 256 or 512.");
      }
      options.copower_kib = static_cast<std::size_t>(kib);
      options.copower = true;
    } else if (argument == "--wait-for") {
      options.actions.push_back(
          {ActionKind::kWaitFor,
           decode_text(require_value(index, argc, argv, argument)), 0});
    } else if (argument == "--send") {
      options.actions.push_back(
          {ActionKind::kSend,
           decode_text(require_value(index, argc, argv, argument)), 0});
    } else if (argument == "--send-file") {
      options.actions.push_back(
          {ActionKind::kSend,
           read_file(require_value(index, argc, argv, argument)), 0});
    } else if (argument == "--swap-floppy-a") {
      options.actions.push_back(
          {ActionKind::kSwapFloppyA,
           require_value(index, argc, argv, argument), 0});
    } else if (argument == "--swap-floppy-b") {
      options.actions.push_back(
          {ActionKind::kSwapFloppyB,
           require_value(index, argc, argv, argument), 0});
    } else if (argument == "--run") {
      options.actions.push_back(
          {ActionKind::kRun, "",
           parse_number(require_value(index, argc, argv, argument),
                        "cycle count")});
    } else if (argument == "--wait-cycles") {
      options.wait_cycles = parse_number(
          require_value(index, argc, argv, argument), "wait cycle count");
      if (options.wait_cycles == 0) {
        throw std::runtime_error("--wait-cycles must be greater than zero.");
      }
    } else if (argument == "--chunk-cycles") {
      options.chunk_cycles = parse_number(
          require_value(index, argc, argv, argument), "chunk cycle count");
      if (options.chunk_cycles == 0) {
        throw std::runtime_error("--chunk-cycles must be greater than zero.");
      }
    } else if (argument == "--output") {
      const std::string value = require_value(index, argc, argv, argument);
      if (value == "json") {
        options.json = true;
      } else if (value == "text") {
        options.json = false;
      } else {
        throw std::runtime_error("--output must be text or json.");
      }
    } else if (argument == "--dump-memory") {
      options.memory_dumps.push_back(parse_memory_dump(
          require_value(index, argc, argv, argument)));
    } else if (argument == "--dump-graphics") {
      options.graphics_dump = require_value(index, argc, argv, argument);
    } else if (argument == "--trace-terminal") {
      options.terminal_trace = require_value(index, argc, argv, argument);
    } else {
      throw std::runtime_error("Unknown argument: " + argument);
    }
  }
  if (!options.help && !options.ipl.has_value()) {
    throw std::runtime_error("--ipl is required.");
  }
  return options;
}

std::string screen_text(const p2000c::P2000cMachine& machine) {
  const auto& screen = machine.terminal().screen();
  return std::string(screen.begin(), screen.end());
}

bool wait_for_text(p2000c::P2000cMachine& machine, std::string_view needle,
                   std::uint64_t timeout, std::uint64_t chunk) {
  if (screen_text(machine).find(needle) != std::string::npos) {
    return true;
  }
  const std::uint64_t start = machine.cycles();
  while (machine.cycles() - start < timeout) {
    const std::uint64_t remaining = timeout - (machine.cycles() - start);
    machine.run_for(std::min(chunk, remaining));
    if (screen_text(machine).find(needle) != std::string::npos) {
      return true;
    }
  }
  return false;
}

const char* graphics_mode_name(p2000c::Terminal::GraphicsMode mode) {
  switch (mode) {
    case p2000c::Terminal::GraphicsMode::kCharacter:
      return "character";
    case p2000c::Terminal::GraphicsMode::kMedium256:
      return "medium-256";
    case p2000c::Terminal::GraphicsMode::kHigh512:
      return "high-512";
  }
  return "unknown";
}

std::string json_string(std::string_view value) {
  std::ostringstream output;
  output << '"';
  constexpr char kHex[] = "0123456789abcdef";
  for (const unsigned char byte : value) {
    switch (byte) {
      case '"':
        output << "\\\"";
        break;
      case '\\':
        output << "\\\\";
        break;
      case '\b':
        output << "\\b";
        break;
      case '\f':
        output << "\\f";
        break;
      case '\n':
        output << "\\n";
        break;
      case '\r':
        output << "\\r";
        break;
      case '\t':
        output << "\\t";
        break;
      default:
        if (byte < 0x20 || byte >= 0x7f) {
          output << "\\u00" << kHex[byte >> 4] << kHex[byte & 0x0f];
        } else {
          output << static_cast<char>(byte);
        }
        break;
    }
  }
  output << '"';
  return output.str();
}

std::string hex_word(std::uint16_t value) {
  std::ostringstream output;
  output << "0x" << std::hex << std::setw(4) << std::setfill('0') << value;
  return output.str();
}

void print_json(const p2000c::P2000cMachine& machine,
                const Options& options, std::string_view status,
                std::string_view message) {
  const auto& terminal = machine.terminal();
  const auto& screen = terminal.screen();
  const std::size_t lit_graphics_bytes = std::count_if(
      terminal.graphic_screen().begin(), terminal.graphic_screen().end(),
      [](std::uint8_t byte) { return byte != 0; });

  std::cout << "{\n"
            << "  \"status\": " << json_string(status) << ",\n";
  if (!message.empty()) {
    std::cout << "  \"message\": " << json_string(message) << ",\n";
  }
  std::cout << "  \"cycles\": " << machine.cycles() << ",\n"
            << "  \"program_counter\": "
            << json_string(hex_word(machine.program_counter())) << ",\n"
            << "  \"copower\": {\"enabled\": "
            << (machine.copower_enabled() ? "true" : "false")
            << ", \"faulted\": "
            << (machine.copower_faulted() ? "true" : "false");
  if (machine.copower_enabled()) {
    const auto [segment, offset] = machine.copower_program_counter();
    std::cout << ", \"program_counter\": "
              << json_string(hex_word(segment) + ":" + hex_word(offset));
  }
  std::cout << "},\n"
            << "  \"cursor\": {\"row\": " << terminal.cursor_row()
            << ", \"column\": " << terminal.cursor_column()
            << ", \"visible\": "
            << (terminal.cursor_visible() ? "true" : "false") << "},\n"
            << "  \"graphics_mode\": "
            << json_string(graphics_mode_name(terminal.graphics_mode()))
            << ",\n"
            << "  \"nonzero_graphics_bytes\": " << lit_graphics_bytes
            << ",\n"
            << "  \"screen\": [\n";
  for (std::size_t row = 0; row < 24; ++row) {
    const std::string_view line(
        reinterpret_cast<const char*>(screen.data() + row * 80), 80);
    std::cout << "    " << json_string(line) << (row == 23 ? "\n" : ",\n");
  }
  std::cout << "  ],\n  \"memory\": [";
  for (std::size_t index = 0; index < options.memory_dumps.size(); ++index) {
    const MemoryDump& dump = options.memory_dumps[index];
    std::ostringstream bytes;
    bytes << std::hex << std::setfill('0');
    for (std::size_t offset = 0; offset < dump.length; ++offset) {
      if (offset != 0) {
        bytes << ' ';
      }
      bytes << std::setw(2)
            << static_cast<unsigned>(machine.read_memory(
                   static_cast<std::uint16_t>(dump.address + offset)));
    }
    std::cout << (index == 0 ? "\n" : ",\n")
              << "    {\"address\": " << json_string(hex_word(dump.address))
              << ", \"bytes\": " << json_string(bytes.str()) << "}";
  }
  if (!options.memory_dumps.empty()) {
    std::cout << '\n';
  }
  std::cout << "  ]\n}\n";
}

void print_text(const p2000c::P2000cMachine& machine,
                const Options& options) {
  const auto& screen = machine.terminal().screen();
  for (std::size_t row = 0; row < 24; ++row) {
    std::string line(screen.begin() + row * 80,
                     screen.begin() + (row + 1) * 80);
    while (!line.empty() && line.back() == ' ') {
      line.pop_back();
    }
    std::cout << line << '\n';
  }
  std::cout << "PC=" << hex_word(machine.program_counter())
            << " cycles=" << machine.cycles()
            << " graphics="
            << graphics_mode_name(machine.terminal().graphics_mode());
  if (machine.copower_enabled()) {
    const auto [segment, offset] = machine.copower_program_counter();
    std::cout << " copower=" << hex_word(segment) << ':' << hex_word(offset)
              << (machine.copower_faulted() ? " faulted" : "");
  }
  std::cout << '\n';
  for (const MemoryDump& dump : options.memory_dumps) {
    std::cout << "Memory " << hex_word(dump.address) << ':';
    for (std::size_t offset = 0; offset < dump.length; ++offset) {
      std::cout << ' ' << std::hex << std::setw(2) << std::setfill('0')
                << static_cast<unsigned>(machine.read_memory(
                       static_cast<std::uint16_t>(dump.address + offset)));
    }
    std::cout << std::dec << '\n';
  }
}

std::filesystem::path media_path(const std::filesystem::path& source,
                                 bool write_through,
                                 TemporaryMedia& temporary_media,
                                 std::string_view drive_name) {
  return write_through ? source : temporary_media.copy(source, drive_name);
}

int run(const Options& options) {
  TemporaryMedia temporary_media;
  p2000c::P2000cMachine machine;
  machine.set_storage_delays_enabled(!options.fast_storage);
  machine.set_copower_enabled(options.copower);
  machine.set_copower_memory_kib(options.copower_kib);
  std::ofstream trace;
  if (options.terminal_trace.has_value()) {
    trace.open(*options.terminal_trace, std::ios::binary);
    if (!trace) {
      throw std::runtime_error("Could not open terminal trace: " +
                               options.terminal_trace->string());
    }
    machine.terminal().set_trace(&trace);
  }
  std::string error;
  if (!machine.load_ipl_rom(*options.ipl, &error)) {
    throw std::runtime_error(error);
  }
  for (std::size_t drive = 0; drive < options.floppies.size(); ++drive) {
    if (!options.floppies[drive].has_value()) {
      continue;
    }
    const std::filesystem::path path = media_path(
        *options.floppies[drive], options.write_through, temporary_media,
        drive == 0 ? "floppy-a" : "floppy-b");
    const bool mounted = drive == 0 ? machine.mount_floppy_a(path, &error)
                                    : machine.mount_floppy_b(path, &error);
    if (!mounted) {
      throw std::runtime_error(error);
    }
  }
  for (std::size_t drive = 0; drive < options.hard_disks.size(); ++drive) {
    if (!options.hard_disks[drive].has_value()) {
      continue;
    }
    const std::filesystem::path path = media_path(
        *options.hard_disks[drive], options.write_through, temporary_media,
        drive == 0 ? "hard-disk-0" : "hard-disk-1");
    if (!machine.mount_hard_disk(drive, path, &error)) {
      throw std::runtime_error(error);
    }
  }

  std::string status = "ok";
  std::string message;
  std::size_t media_swap_count = 0;
  for (const Action& action : options.actions) {
    if (action.kind == ActionKind::kSend) {
      for (const unsigned char byte : action.text) {
        machine.queue_key(byte);
      }
    } else if (action.kind == ActionKind::kRun) {
      machine.run_for(action.cycles);
    } else if (action.kind == ActionKind::kSwapFloppyA ||
               action.kind == ActionKind::kSwapFloppyB) {
      const std::size_t drive =
          action.kind == ActionKind::kSwapFloppyA ? 0 : 1;
      const std::filesystem::path source(action.text);
      const std::filesystem::path path = media_path(
          source, options.write_through, temporary_media,
          "floppy-swap-" + std::to_string(media_swap_count++));
      const bool mounted = drive == 0 ? machine.mount_floppy_a(path, &error)
                                      : machine.mount_floppy_b(path, &error);
      if (!mounted) {
        throw std::runtime_error(error);
      }
    } else if (!wait_for_text(machine, action.text, options.wait_cycles,
                              options.chunk_cycles)) {
      status = "timeout";
      message = "Screen text did not appear before the cycle limit: " +
                action.text;
      break;
    }
  }

  if (options.graphics_dump.has_value()) {
    std::ofstream output(*options.graphics_dump, std::ios::binary);
    const auto& graphics = machine.terminal().graphic_screen();
    output.write(reinterpret_cast<const char*>(graphics.data()),
                 static_cast<std::streamsize>(graphics.size()));
    if (!output) {
      throw std::runtime_error("Could not write graphics dump: " +
                               options.graphics_dump->string());
    }
  }
  if (options.json) {
    print_json(machine, options, status, message);
  } else {
    print_text(machine, options);
  }
  if (status != "ok") {
    std::cerr << message << '\n';
    return 3;
  }
  return 0;
}

}  // namespace

int main(int argc, char* argv[]) {
  try {
    const Options options = parse_options(argc, argv);
    if (options.help) {
      print_usage(std::cout);
      return 0;
    }
    return run(options);
  } catch (const std::exception& exception) {
    std::cerr << "p2000c_cli: " << exception.what() << "\n\n";
    print_usage(std::cerr);
    return 2;
  }
}

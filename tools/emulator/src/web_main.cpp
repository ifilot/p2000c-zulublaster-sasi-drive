#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

#include <emscripten/emscripten.h>

#include "core/p2000c_machine.h"

namespace {

std::unique_ptr<p2000c::P2000cMachine> machine;
std::string last_error;

int fail(const std::string &message) {
  last_error = message;
  machine.reset();
  return 0;
}

} // namespace

extern "C" {

EMSCRIPTEN_KEEPALIVE int p2000c_init() {
  machine = std::make_unique<p2000c::P2000cMachine>();
  if (!machine->load_ipl_rom("/IPLDUMP.BIN", &last_error)) {
    return fail(last_error);
  }
  if (!machine->mount_hard_disk(0, "/HD0_256.hda", &last_error) ||
      !machine->mount_hard_disk(1, "/HD1_256.hda", &last_error)) {
    return fail(last_error);
  }
  machine->set_storage_delays_enabled(false);
  machine->reset();
  last_error.clear();
  return 1;
}

EMSCRIPTEN_KEEPALIVE const char *p2000c_last_error() {
  return last_error.c_str();
}

EMSCRIPTEN_KEEPALIVE void p2000c_reset() {
  if (machine) {
    machine->reset();
  }
}

EMSCRIPTEN_KEEPALIVE void p2000c_run(std::uint32_t cycles) {
  if (machine) {
    machine->run_for(cycles);
  }
}

EMSCRIPTEN_KEEPALIVE void p2000c_key(std::uint32_t value) {
  if (machine && value <= 0xff) {
    machine->queue_key(static_cast<std::uint8_t>(value));
  }
}

EMSCRIPTEN_KEEPALIVE std::uintptr_t p2000c_screen() {
  return machine ? reinterpret_cast<std::uintptr_t>(
                       machine->terminal().screen().data())
                 : 0;
}

EMSCRIPTEN_KEEPALIVE std::uintptr_t p2000c_attributes() {
  return machine ? reinterpret_cast<std::uintptr_t>(
                       machine->terminal().attributes().data())
                 : 0;
}

EMSCRIPTEN_KEEPALIVE std::uintptr_t p2000c_graphics() {
  return machine ? reinterpret_cast<std::uintptr_t>(
                       machine->terminal().graphic_screen().data())
                 : 0;
}

EMSCRIPTEN_KEEPALIVE std::uint32_t p2000c_revision() {
  return machine ? static_cast<std::uint32_t>(machine->terminal().revision())
                 : 0;
}

EMSCRIPTEN_KEEPALIVE int p2000c_graphics_mode() {
  return machine ? static_cast<int>(machine->terminal().graphics_mode()) : 0;
}

EMSCRIPTEN_KEEPALIVE int p2000c_cursor_row() {
  return machine ? machine->terminal().cursor_row() : 0;
}

EMSCRIPTEN_KEEPALIVE int p2000c_cursor_column() {
  return machine ? machine->terminal().cursor_column() : 0;
}

EMSCRIPTEN_KEEPALIVE int p2000c_cursor_visible() {
  return machine && machine->terminal().cursor_visible() ? 1 : 0;
}

} // extern "C"

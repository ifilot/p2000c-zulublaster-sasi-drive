#include "core/copower_board.h"

#include <utility>
#include <stdexcept>

extern "C" {
#include "i8088.h"
}

namespace p2000c {
namespace {

constexpr std::uint32_t kCommonMemoryBase = 0xf0000;
constexpr std::uint64_t kMainClockMhz = 4;
constexpr std::uint64_t kCoPowerClockMhz = 5;
constexpr std::uint64_t kNominal8088ClocksPerInstruction = 8;

}  // namespace

CoPowerBoard::CoPowerBoard(SharedRead shared_read, SharedWrite shared_write,
                           Z80Interrupt z80_interrupt)
    : shared_read_(std::move(shared_read)),
      shared_write_(std::move(shared_write)),
      z80_interrupt_(std::move(z80_interrupt)) {
  const i8088_callbacks callbacks = {
      this, &CoPowerBoard::cpu_read, &CoPowerBoard::cpu_write,
      &CoPowerBoard::cpu_port_in, &CoPowerBoard::cpu_port_out};
  cpu_ = i8088_create(callbacks);
}

CoPowerBoard::~CoPowerBoard() { i8088_destroy(cpu_); }

void CoPowerBoard::set_memory_kib(std::size_t kib) {
  if (kib != 256 && kib != 512) {
    throw std::invalid_argument("CoPower RAM must be 256 or 512 KiB.");
  }
  local_ram_.assign(kib * 1024, 0);
  reset();
}

void CoPowerBoard::set_enabled(bool enabled) {
  enabled_ = enabled;
  reset();
}

void CoPowerBoard::reset() {
  i8088_reset(cpu_);
  held_in_reset_ = true;
  common_memory_locked_ = false;
  clock_accumulator_ = 0;
}

void CoPowerBoard::run_for(std::uint64_t z80_t_states) {
  if (!enabled_ || held_in_reset_ || common_memory_locked_ ||
      i8088_faulted(cpu_) || i8088_halted(cpu_)) {
    return;
  }

  clock_accumulator_ += z80_t_states * kCoPowerClockMhz;
  constexpr std::uint64_t kStepThreshold =
      kMainClockMhz * kNominal8088ClocksPerInstruction;
  while (clock_accumulator_ >= kStepThreshold) {
    i8088_step(cpu_);
    clock_accumulator_ -= kStepThreshold;
    if (i8088_faulted(cpu_) || i8088_halted(cpu_)) {
      break;
    }
  }
}

void CoPowerBoard::write_interrupt_vector(std::uint8_t vector) {
  if (enabled_ && !held_in_reset_ && !common_memory_locked_) {
    i8088_interrupt(cpu_, vector);
  }
}

void CoPowerBoard::write_control(std::uint8_t value) {
  if (!enabled_) {
    return;
  }
  switch (value) {
    case 1:
      i8088_reset(cpu_);
      held_in_reset_ = true;
      common_memory_locked_ = false;
      clock_accumulator_ = 0;
      break;
    case 2:
      held_in_reset_ = false;
      common_memory_locked_ = false;
      break;
    case 3:
      common_memory_locked_ = true;
      break;
    default:
      break;
  }
}

bool CoPowerBoard::faulted() const { return i8088_faulted(cpu_); }

std::uint16_t CoPowerBoard::program_counter() const {
  return i8088_ip(cpu_);
}

std::uint16_t CoPowerBoard::code_segment() const {
  return i8088_cs(cpu_);
}

std::uint8_t CoPowerBoard::cpu_read(void* context, std::uint32_t address) {
  return static_cast<CoPowerBoard*>(context)->read(address);
}

void CoPowerBoard::cpu_write(void* context, std::uint32_t address,
                             std::uint8_t value) {
  static_cast<CoPowerBoard*>(context)->write(address, value);
}

std::uint16_t CoPowerBoard::cpu_port_in(void*, std::uint16_t, bool word) {
  return word ? 0xffff : 0xff;
}

void CoPowerBoard::cpu_port_out(void* context, std::uint16_t, std::uint16_t,
                                bool) {
  auto* board = static_cast<CoPowerBoard*>(context);
  if (board->enabled_ && board->z80_interrupt_) {
    board->z80_interrupt_();
  }
}

std::uint8_t CoPowerBoard::read(std::uint32_t address) const {
  address &= 0xfffff;
  if (address < local_ram_.size()) {
    return local_ram_[address];
  }
  if (address >= kCommonMemoryBase) {
    return shared_read_(static_cast<std::uint16_t>(address));
  }
  return 0xff;
}

void CoPowerBoard::write(std::uint32_t address, std::uint8_t value) {
  address &= 0xfffff;
  if (address < local_ram_.size()) {
    local_ram_[address] = value;
  } else if (address >= kCommonMemoryBase) {
    shared_write_(static_cast<std::uint16_t>(address), value);
  }
}

}  // namespace p2000c

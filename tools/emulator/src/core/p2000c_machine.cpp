#include "core/p2000c_machine.h"

#include <algorithm>
#include <fstream>
#include <iterator>
#include <numeric>
#include <utility>
#include <vector>

extern "C" {
#include "z80.h"
}

namespace p2000c {
namespace {

void set_error(std::string* error, const std::string& message) {
  if (error != nullptr) {
    *error = message;
  }
}

}  // namespace

P2000cMachine::P2000cMachine()
    : cpu_(std::make_unique<z80>()),
      copower_(
          [this](std::uint16_t address) { return ram_[address]; },
          [this](std::uint16_t address, std::uint8_t value) {
            write_memory(address, value);
          },
          [this]() { request_interrupt(0xdc, false); }) {
  z80_init(cpu_.get());
  cpu_->read_byte = &P2000cMachine::cpu_read;
  cpu_->write_byte = &P2000cMachine::cpu_write;
  cpu_->port_in = &P2000cMachine::cpu_port_in;
  cpu_->port_out = &P2000cMachine::cpu_port_out;
  cpu_->userdata = this;
  reset();
}

P2000cMachine::~P2000cMachine() = default;

bool P2000cMachine::load_ipl_rom(const std::filesystem::path& path,
                                 std::string* error) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    set_error(error, "Could not open mainboard IPL ROM: " + path.string());
    return false;
  }
  std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(input)),
                                  std::istreambuf_iterator<char>());
  return load_ipl_rom(bytes, error);
}

bool P2000cMachine::load_ipl_rom(std::span<const std::uint8_t> bytes,
                                 std::string* error) {
  if (bytes.size() != kIplRomSize) {
    set_error(error, "The mainboard IPL ROM must be exactly 4096 bytes.");
    return false;
  }
  std::uint16_t checksum = 0;
  for (std::size_t index = 0; index < kIplRomSize - 2; ++index) {
    checksum = static_cast<std::uint16_t>(checksum + bytes[index]);
  }
  const std::uint16_t stored_checksum =
      static_cast<std::uint16_t>(bytes[kIplRomSize - 2]) |
      static_cast<std::uint16_t>(bytes[kIplRomSize - 1] << 8);
  if (checksum != stored_checksum) {
    set_error(error, "The mainboard IPL ROM checksum is invalid.");
    return false;
  }
  std::copy(bytes.begin(), bytes.end(), ipl_rom_.begin());
  has_ipl_rom_ = true;
  reset();
  return true;
}

bool P2000cMachine::mount_floppy_a(const std::filesystem::path& path,
                                   std::string* error) {
  return mount_floppy(0, path, error);
}

bool P2000cMachine::mount_floppy_b(const std::filesystem::path& path,
                                   std::string* error) {
  return mount_floppy(1, path, error);
}

bool P2000cMachine::mount_floppy(std::size_t drive,
                                 const std::filesystem::path& path,
                                 std::string* error) {
  std::optional<RawDiskImage> image =
      RawDiskImage::open(path, RawDiskImage::Kind::kFloppy, error);
  if (!image.has_value()) {
    return false;
  }
  floppy_drives_[drive] = std::move(*image);
  fdc_tracks_[drive] = 0;
  fdc_sides_[drive] = 0;
  return true;
}

bool P2000cMachine::mount_hard_disk(std::size_t drive,
                                    const std::filesystem::path& path,
                                    std::string* error) {
  if (drive >= hard_disks_.size()) {
    set_error(error, "The P2000C supports two physical SASI hard disks.");
    return false;
  }
  std::optional<RawDiskImage> image =
      RawDiskImage::open(path, RawDiskImage::Kind::kHardDisk, error);
  if (!image.has_value()) {
    return false;
  }
  hard_disks_[drive] = std::move(*image);
  sasi_blocks_[drive] = 0;
  return true;
}

bool P2000cMachine::unmount_hard_disk(std::size_t drive) {
  if (drive >= hard_disks_.size()) {
    return false;
  }
  hard_disks_[drive].reset();
  sasi_blocks_[drive] = 0;
  sasi_phase_ = SasiPhase::kBusFree;
  sasi_command_length_ = 0;
  sasi_status_ = 0;
  return true;
}

const RawDiskImage* P2000cMachine::floppy_drive(std::uint8_t drive) const {
  if (drive >= floppy_drives_.size() || !floppy_drives_[drive].has_value()) {
    return nullptr;
  }
  return &*floppy_drives_[drive];
}

void P2000cMachine::reset() {
  z80_init(cpu_.get());
  cpu_->read_byte = &P2000cMachine::cpu_read;
  cpu_->write_byte = &P2000cMachine::cpu_write;
  cpu_->port_in = &P2000cMachine::cpu_port_in;
  cpu_->port_out = &P2000cMachine::cpu_port_out;
  cpu_->userdata = this;
  memory_manager_ = 0;
  memory_written_.reset();
  memory_page_write_counts_.fill(0);
  terminal_.reset();
  dma_channels_.fill({});
  interrupt_queue_.clear();
  timed_interrupts_.clear();
  fdc_command_.clear();
  fdc_result_.clear();
  dma_high_byte_ = false;
  dma_read_high_byte_ = false;
  handshake_started_ = false;
  terminal_interrupt_requested_ = false;
  sio_b_polling_ = false;
  sio_b_dtr_ = false;
  fdc_reset_released_ = false;
  fdc_sense_pending_ = false;
  dma_mode_ = 0;
  dma_status_ = 0;
  fdc_output_ = 0;
  fdc_sense_status_ = 0xc0;
  fdc_tracks_.fill(0);
  fdc_sides_.fill(0);
  fdc_sense_track_ = 0;
  sasi_phase_ = SasiPhase::kBusFree;
  sasi_command_.fill(0);
  sasi_command_length_ = 0;
  sasi_status_ = 0;
  sasi_blocks_.fill(0);
  sio_b_register_ = 0;
  sio_b_receive_byte_ = 0;
  sio_b_receive_ready_ = false;
  total_cycles_ = 0;
  next_timer_cycle_ = kTimerPeriod;
  storage_busy_until_ = 0;
  fdc_ready_cycle_ = 0;
  copower_.reset();
}

void P2000cMachine::run_for(std::uint64_t t_states) {
  if (!has_ipl_rom_) {
    return;
  }
  while (t_states > 0) {
    const unsigned long previous_cycles = cpu_->cyc;
    update_devices();
    z80_step(cpu_.get());
    const unsigned long instruction_cycles = cpu_->cyc - previous_cycles;
    total_cycles_ += instruction_cycles;
    copower_.run_for(instruction_cycles);
    if (instruction_cycles >= t_states) {
      break;
    }
    t_states -= instruction_cycles;
  }
}

void P2000cMachine::begin_storage_activity(const StorageActivity& activity,
                                           bool apply_latency) {
  if (storage_activity_handler_) {
    storage_activity_handler_(activity);
  }
  if (storage_delays_enabled_ &&
      activity.device == StorageDevice::kFloppy && apply_latency &&
      activity.duration_ms > 0) {
    const std::uint64_t duration =
        static_cast<std::uint64_t>(activity.duration_ms) * 4'000;
    storage_busy_until_ =
        std::max(storage_busy_until_, total_cycles_ + duration);
  }
}

std::uint16_t P2000cMachine::program_counter() const { return cpu_->pc; }

std::uint64_t P2000cMachine::cycles() const { return total_cycles_; }

std::uint8_t P2000cMachine::read_memory(std::uint16_t address) const {
  if (memory_manager_ == 0 && address < kIplRomSize) {
    return ipl_rom_[address];
  }
  return ram_[address];
}

void P2000cMachine::write_memory(std::uint16_t address, std::uint8_t value) {
  ram_[address] = value;
  if (!memory_written_.test(address)) {
    memory_written_.set(address);
    ++memory_page_write_counts_[address >> 8];
  }
}

std::uint8_t P2000cMachine::cpu_read(void* context, std::uint16_t address) {
  return static_cast<P2000cMachine*>(context)->read_memory(address);
}

void P2000cMachine::cpu_write(void* context, std::uint16_t address,
                              std::uint8_t value) {
  static_cast<P2000cMachine*>(context)->write_memory(address, value);
}

std::uint8_t P2000cMachine::cpu_port_in(z80* cpu, std::uint8_t port) {
  auto* machine = static_cast<P2000cMachine*>(cpu->userdata);
  if (port <= 0x08) {
    return machine->read_dma(port);
  }
  switch (port) {
    case 0x14:
      return 0;
    case 0x15:
      return 0x85;
    case 0x16:
    case 0x17:
      return machine->read_sasi_data();
    case 0x18:
    case 0x19:
      return machine->read_sasi_control();
    case 0x1a:
      return machine->fdc_status();
    case 0x1b:
      if (machine->fdc_result_.empty()) {
        return 0xff;
      } else {
        const std::uint8_t value = machine->fdc_result_.front();
        machine->fdc_result_.pop_front();
        return value;
      }
    case 0x28:
      return 0;
    case 0x29:
      return 0x04;
    case 0x2a:
    case 0x2b:
      return machine->read_terminal_sio(port);
    default:
      return 0xff;
  }
}

void P2000cMachine::cpu_port_out(z80* cpu, std::uint8_t port,
                                 std::uint8_t value) {
  auto* machine = static_cast<P2000cMachine*>(cpu->userdata);
  if (port <= 0x08) {
    machine->write_dma(port, value);
    return;
  }
  switch (port) {
    case 0x16:
    case 0x17:
      machine->write_sasi_data(value);
      break;
    case 0x18:
    case 0x19:
      machine->write_sasi_control(value);
      break;
    case 0x1b:
      machine->write_fdc(value);
      break;
    case 0x1e:
      machine->write_memory_manager(value);
      break;
    case 0x1f: {
      const bool was_released = (machine->fdc_output_ & 0x10) != 0;
      const bool motor_was_on = (machine->fdc_output_ & 0x20) != 0;
      machine->fdc_output_ = value;
      const bool is_released = (value & 0x10) != 0;
      if (!was_released && is_released) {
        machine->release_fdc_reset();
      }
      if (!is_released) {
        machine->fdc_reset_released_ = false;
      }
      if (!motor_was_on && (value & 0x20) != 0) {
        machine->begin_storage_activity(
            {StorageDevice::kFloppy, StorageOperation::kMotorStart, 0, 0,
             400},
            false);
      } else if (motor_was_on && (value & 0x20) == 0) {
        machine->begin_storage_activity(
            {StorageDevice::kFloppy, StorageOperation::kMotorStop, 0, 0, 100},
            false);
      }
      break;
    }
    case 0x2a:
    case 0x2b:
      machine->write_terminal_sio(port, value);
      break;
    case 0x30:
      machine->copower_.write_interrupt_vector(value);
      break;
    case 0x31:
      machine->copower_.write_control(value);
      break;
    default:
      break;
  }
}

void P2000cMachine::write_memory_manager(std::uint8_t value) {
  // The manual defines MM2:MM1=00 as the IPL overlay and 10 as internal RAM.
  // Writes always reach the underlying RAM, including while ROM is visible.
  memory_manager_ = value & 0x03;
}

void P2000cMachine::update_devices() {
  if (!handshake_started_ && total_cycles_ >= kHandshakeDelay) {
    terminal_.begin_handshake();
    handshake_started_ = true;
  }
  if (terminal_.has_input() && (sio_b_dtr_ || sio_b_polling_) &&
      !sio_b_receive_ready_ &&
      !terminal_interrupt_requested_) {
    sio_b_receive_byte_ = terminal_.take_input();
    sio_b_receive_ready_ = true;
    if (!sio_b_polling_) {
      request_interrupt(0xe4);
      terminal_interrupt_requested_ = true;
    }
  }
  while (total_cycles_ >= next_timer_cycle_) {
    request_interrupt(0xd8);
    next_timer_cycle_ += kTimerPeriod;
  }
  while (!timed_interrupts_.empty() &&
         timed_interrupts_.front().due_cycle <= total_cycles_) {
    if (interrupt_queue_.size() < 32) {
      interrupt_queue_.push_back(timed_interrupts_.front().vector);
    }
    timed_interrupts_.pop_front();
  }
  if (cpu_->iff1 && !cpu_->int_pending && !interrupt_queue_.empty()) {
    z80_gen_int(cpu_.get(), interrupt_queue_.front());
    interrupt_queue_.pop_front();
  }
}

void P2000cMachine::request_interrupt(std::uint8_t vector,
                                     bool apply_floppy_latency) {
  if (apply_floppy_latency && (vector == 0xd6 || vector == 0xde) &&
      total_cycles_ < storage_busy_until_) {
    timed_interrupts_.push_back({storage_busy_until_, vector});
    return;
  }
  if (interrupt_queue_.size() < 32) {
    interrupt_queue_.push_back(vector);
  }
}

std::uint8_t P2000cMachine::read_dma(std::uint8_t port) {
  if (port == 0x08) {
    const std::uint8_t status = dma_status_;
    dma_status_ = 0;
    dma_read_high_byte_ = false;
    return status;
  }
  const DmaChannel& channel = dma_channels_[port / 2];
  const std::uint16_t value = (port & 1) == 0 ? channel.address : channel.count;
  const std::uint8_t result = dma_read_high_byte_
                                  ? static_cast<std::uint8_t>(value >> 8)
                                  : static_cast<std::uint8_t>(value);
  dma_read_high_byte_ = !dma_read_high_byte_;
  return result;
}

void P2000cMachine::write_dma(std::uint8_t port, std::uint8_t value) {
  if (port == 0x08) {
    dma_mode_ = value;
    dma_high_byte_ = false;
    dma_read_high_byte_ = false;
    if ((dma_mode_ & 0x08) != 0) {
      run_terminal_dma();
    }
    return;
  }
  DmaChannel& channel = dma_channels_[port / 2];
  std::uint16_t& target = (port & 1) == 0 ? channel.address : channel.count;
  if (dma_high_byte_) {
    target = static_cast<std::uint16_t>((target & 0x00ff) | (value << 8));
  } else {
    target = static_cast<std::uint16_t>((target & 0xff00) | value);
  }
  dma_high_byte_ = !dma_high_byte_;
}

void P2000cMachine::run_terminal_dma() {
  DmaChannel& channel = dma_channels_[3];
  const std::size_t length = (channel.count & 0x3fff) + 1;
  for (std::size_t index = 0; index < length; ++index) {
    terminal_.receive(read_memory(channel.address++));
  }
  channel.count = 0x3fff;
  dma_mode_ &= ~0x08;
  dma_status_ |= 0x08;
  request_interrupt(0xd6);
}

bool P2000cMachine::run_floppy_dma(std::span<const std::uint8_t> data,
                                   bool apply_floppy_latency) {
  if ((dma_mode_ & 0x01) == 0) {
    return false;
  }
  DmaChannel& channel = dma_channels_[0];
  const std::size_t length = (channel.count & 0x3fff) + 1;
  if (data.size() < length) {
    return false;
  }
  for (std::size_t index = 0; index < length; ++index) {
    write_memory(channel.address++, data[index]);
  }
  channel.count = 0x3fff;
  dma_mode_ &= ~0x01;
  dma_status_ |= 0x01;
  request_interrupt(0xd6, apply_floppy_latency);
  return true;
}

std::optional<std::vector<std::uint8_t>> P2000cMachine::take_disk_dma(
    bool apply_floppy_latency) {
  if ((dma_mode_ & 0x01) == 0) {
    return std::nullopt;
  }
  DmaChannel& channel = dma_channels_[0];
  const std::size_t length = (channel.count & 0x3fff) + 1;
  std::vector<std::uint8_t> data;
  data.reserve(length);
  for (std::size_t index = 0; index < length; ++index) {
    data.push_back(read_memory(channel.address++));
  }
  channel.count = 0x3fff;
  dma_mode_ &= ~0x01;
  dma_status_ |= 0x01;
  request_interrupt(0xd6, apply_floppy_latency);
  return data;
}

std::uint8_t P2000cMachine::fdc_status() const {
  if (!fdc_reset_released_) {
    return 0;
  }
  if (total_cycles_ < fdc_ready_cycle_) {
    return 0x10;  // Controller busy; result phase begins after the access.
  }
  return fdc_result_.empty() ? 0x80 : 0xc0;
}

void P2000cMachine::write_fdc(std::uint8_t value) {
  if (!fdc_reset_released_) {
    return;
  }
  fdc_command_.push_back(value);
  if (fdc_command_.size() == fdc_command_size(fdc_command_.front())) {
    complete_fdc_command();
    fdc_command_.clear();
  }
}

void P2000cMachine::complete_fdc_command() {
  const std::uint8_t command = fdc_command_.front() & 0x1f;
  if (command == 0x03) {
    return;
  }
  if (command == 0x08) {
    fdc_result_.push_back(fdc_sense_pending_ ? fdc_sense_status_ : 0x80);
    fdc_result_.push_back(fdc_sense_track_);
    fdc_sense_pending_ = false;
    return;
  }
  if (command == 0x07 || command == 0x0f) {
    const std::uint8_t drive = fdc_command_[1] & 0x03;
    const RawDiskImage* image = floppy_drive(drive);
    const int old_track =
        drive < fdc_tracks_.size() ? fdc_tracks_[drive] : 0;
    const int new_track = command == 0x0f ? fdc_command_[2] : 0;
    if (drive < fdc_tracks_.size()) {
      fdc_tracks_[drive] = command == 0x0f ? fdc_command_[2] : 0;
      fdc_sense_track_ = fdc_tracks_[drive];
    } else {
      fdc_sense_track_ = 0;
    }
    const bool drive_ready = image != nullptr;
    fdc_sense_status_ =
        static_cast<std::uint8_t>((drive_ready ? 0x20 : 0x48) | drive);
    fdc_sense_pending_ = true;
    const int distance = std::abs(new_track - old_track);
    begin_storage_activity(
        {StorageDevice::kFloppy, StorageOperation::kSeek, drive, distance,
         15 + std::max(1, distance) * 6},
        drive_ready);
    fdc_ready_cycle_ = storage_busy_until_;
    request_interrupt(0xde);
    return;
  }

  if (command == 0x06 && fdc_command_.size() == 9) {
    const std::uint8_t drive = fdc_command_[1] & 0x03;
    const std::uint8_t cylinder = fdc_command_[2];
    const std::uint8_t head = fdc_command_[3];
    const std::uint8_t first_sector = fdc_command_[4];
    const std::uint8_t size_code = fdc_command_[5];
    const std::uint8_t last_sector = fdc_command_[6];
    const std::size_t dma_length = (dma_channels_[0].count & 0x3fff) + 1;
    const RawDiskImage* image = floppy_drive(drive);
    const std::size_t sector_size =
        image != nullptr
            ? image->floppy_sector_size()
            : (std::size_t{128} << std::min<std::uint8_t>(size_code, 7));
    const int sectors = static_cast<int>(
        (dma_length + sector_size - 1) / sector_size);
    const std::uint8_t result_sector = static_cast<std::uint8_t>(
        std::min<std::size_t>(last_sector,
                              first_sector +
                                  (dma_length + sector_size - 1) /
                                      sector_size -
                                  1));
    std::vector<std::uint8_t> track_data;
    if (drive < fdc_tracks_.size()) {
      fdc_tracks_[drive] = cylinder;
      fdc_sides_[drive] = head;
    }
    const std::uint16_t final_data_sector =
        static_cast<std::uint16_t>(first_sector + sectors - 1);
    bool media_ok = image != nullptr && final_data_sector <= last_sector;
    for (std::uint16_t id = first_sector;
         media_ok && id <= final_data_sector; ++id) {
      const std::span<const std::uint8_t> sector =
          image->floppy_sector(cylinder, head, static_cast<std::uint8_t>(id));
      if (sector.empty()) {
        media_ok = false;
      } else {
        track_data.insert(track_data.end(), sector.begin(), sector.end());
      }
    }
    begin_storage_activity(
        {StorageDevice::kFloppy, StorageOperation::kRead, drive, 0,
         105 + sectors * 13},
        image != nullptr);
    fdc_ready_cycle_ = storage_busy_until_;
    media_ok = media_ok && run_floppy_dma(track_data);
    if (media_ok) {
      fdc_result_.insert(fdc_result_.end(),
                         {static_cast<std::uint8_t>((head << 2) | drive), 0, 0,
                          cylinder, head, result_sector, size_code});
    } else {
      fdc_result_.insert(fdc_result_.end(),
                         {static_cast<std::uint8_t>(0x48 | (head << 2) | drive),
                          0x04, 0, cylinder, head, first_sector, size_code});
    }
    request_interrupt(0xde);
    return;
  }

  if (command == 0x05 && fdc_command_.size() == 9) {
    const std::uint8_t drive = fdc_command_[1] & 0x03;
    const std::uint8_t cylinder = fdc_command_[2];
    const std::uint8_t head = fdc_command_[3];
    const std::uint8_t first_sector = fdc_command_[4];
    const std::uint8_t size_code = fdc_command_[5];
    const std::uint8_t last_sector = fdc_command_[6];
    const std::size_t dma_length = (dma_channels_[0].count & 0x3fff) + 1;
    RawDiskImage* image =
        drive < floppy_drives_.size() && floppy_drives_[drive].has_value()
            ? &*floppy_drives_[drive]
            : nullptr;
    const std::size_t sector_size =
        image != nullptr
            ? image->floppy_sector_size()
            : (std::size_t{128} << std::min<std::uint8_t>(size_code, 7));
    const int requested_sectors = static_cast<int>(
        (dma_length + sector_size - 1) / sector_size);
    const std::uint8_t result_sector = static_cast<std::uint8_t>(
        std::min<std::size_t>(last_sector,
                              first_sector +
                                  (dma_length + sector_size - 1) /
                                      sector_size -
                                  1));
    if (drive < fdc_tracks_.size()) {
      fdc_tracks_[drive] = cylinder;
      fdc_sides_[drive] = head;
    }
    begin_storage_activity(
        {StorageDevice::kFloppy, StorageOperation::kWrite, drive, 0,
         105 + requested_sectors * 13},
        image != nullptr);
    fdc_ready_cycle_ = storage_busy_until_;
    std::optional<std::vector<std::uint8_t>> data = take_disk_dma();
    const std::size_t sectors = data.has_value()
                                    ? data->size() / sector_size
                                    : 0;
    bool media_ok = image != nullptr && data.has_value() && sectors != 0 &&
                    data->size() % sector_size == 0 &&
                    first_sector + sectors - 1 <= last_sector;
    std::string error;
    for (std::size_t index = 0; media_ok && index < sectors; ++index) {
      media_ok = image->write_floppy_sector(
          cylinder, head, static_cast<std::uint8_t>(first_sector + index),
          std::span<const std::uint8_t>(*data).subspan(
              index * sector_size, sector_size),
          &error);
    }
    if (media_ok) {
      fdc_result_.insert(fdc_result_.end(),
                         {static_cast<std::uint8_t>((head << 2) | drive), 0, 0,
                          cylinder, head, result_sector, size_code});
    } else {
      fdc_result_.insert(fdc_result_.end(),
                         {static_cast<std::uint8_t>(0x48 | (head << 2) | drive),
                          0x04, 0, cylinder, head, first_sector, size_code});
    }
    request_interrupt(0xde);
    return;
  }

  fdc_result_.push_back(0x80);
}

std::size_t P2000cMachine::fdc_command_size(std::uint8_t command) {
  switch (command & 0x1f) {
    case 0x03:
      return 3;
    case 0x04:
    case 0x07:
    case 0x0a:
      return 2;
    case 0x08:
      return 1;
    case 0x0f:
      return 3;
    case 0x05:
    case 0x06:
    case 0x09:
    case 0x0c:
      return 9;
    case 0x0d:
      return 6;
    default:
      return 1;
  }
}

void P2000cMachine::release_fdc_reset() {
  fdc_reset_released_ = true;
  fdc_command_.clear();
  fdc_result_.clear();
  fdc_sense_status_ = 0xc0;
  fdc_sense_track_ = 0;
  fdc_sense_pending_ = true;
  request_interrupt(0xde);
}

std::uint8_t P2000cMachine::read_sasi_control() const {
  switch (sasi_phase_) {
    case SasiPhase::kBusFree:
      return 0;
    case SasiPhase::kCommand:
      return 0x8b;  // REQ, C/D and BSY.
    case SasiPhase::kStatus:
      return 0x9b;  // REQ, C/D, BSY and I/O.
    case SasiPhase::kMessage:
      return 0x9f;  // Status signals plus MSG.
  }
  return 0;
}

void P2000cMachine::write_sasi_control(std::uint8_t value) {
  if ((value & 0x08) != 0) {
    sasi_phase_ = SasiPhase::kBusFree;
    sasi_command_length_ = 0;
    sasi_status_ = 0;
    return;
  }
  if ((value & 0x04) != 0 && sasi_phase_ == SasiPhase::kBusFree &&
      std::any_of(hard_disks_.begin(), hard_disks_.end(),
                  [](const auto& disk) { return disk.has_value(); })) {
    sasi_phase_ = SasiPhase::kCommand;
    sasi_command_length_ = 0;
    sasi_status_ = 0;
  }
}

std::uint8_t P2000cMachine::read_sasi_data() {
  if (sasi_phase_ == SasiPhase::kStatus) {
    sasi_phase_ = SasiPhase::kMessage;
    return sasi_status_;
  }
  if (sasi_phase_ == SasiPhase::kMessage) {
    sasi_phase_ = SasiPhase::kBusFree;
    return 0;
  }
  return 0xff;
}

void P2000cMachine::write_sasi_data(std::uint8_t value) {
  if (sasi_phase_ != SasiPhase::kCommand ||
      sasi_command_length_ >= sasi_command_.size()) {
    return;
  }
  sasi_command_[sasi_command_length_++] = value;
  if (sasi_command_length_ == sasi_command_.size()) {
    execute_sasi_command();
  }
}

void P2000cMachine::execute_sasi_command() {
  const std::uint8_t opcode = sasi_command_[0] & 0x1f;
  const std::size_t unit = (sasi_command_[1] >> 5) & 0x07;
  const std::size_t lba =
      (static_cast<std::size_t>(sasi_command_[1] & 0x1f) << 16) |
      (static_cast<std::size_t>(sasi_command_[2]) << 8) | sasi_command_[3];
  const std::size_t block_count =
      sasi_command_[4] == 0 ? 256 : sasi_command_[4];
  RawDiskImage* disk = unit < hard_disks_.size() && hard_disks_[unit].has_value()
                           ? &*hard_disks_[unit]
                           : nullptr;
  bool okay = disk != nullptr;
  if (unit < sasi_blocks_.size()) {
    sasi_blocks_[unit] = lba + block_count - 1;
  }

  if (okay && opcode == 0x08) {
    begin_storage_activity(
        {StorageDevice::kHardDisk, StorageOperation::kRead, unit, 0,
         60 + static_cast<int>(block_count)},
        false);
    const std::span<const std::uint8_t> data = disk->blocks(lba, block_count);
    okay = !data.empty() && run_floppy_dma(data, false);
  } else if (okay && opcode == 0x0a) {
    begin_storage_activity(
        {StorageDevice::kHardDisk, StorageOperation::kWrite, unit, 0,
         60 + static_cast<int>(block_count)},
        false);
    std::optional<std::vector<std::uint8_t>> data = take_disk_dma(false);
    std::string error;
    okay = data.has_value() &&
           data->size() == block_count * RawDiskImage::kSectorSize &&
           disk->write_blocks(lba, *data, &error);
  } else if (opcode != 0x00 && opcode != 0x01 && opcode != 0x0b) {
    okay = false;
  }

  sasi_status_ = okay ? 0 : 0x02;
  sasi_phase_ = SasiPhase::kStatus;
  request_interrupt(0xde, false);
}

std::uint8_t P2000cMachine::read_terminal_sio(std::uint8_t port) {
  if (port == 0x2b) {
    return static_cast<std::uint8_t>(0x04 | (sio_b_receive_ready_ ? 0x01 : 0));
  }
  sio_b_receive_ready_ = false;
  sio_b_polling_ = false;
  return sio_b_receive_byte_;
}

void P2000cMachine::write_terminal_sio(std::uint8_t port, std::uint8_t value) {
  if (port == 0x2a) {
    terminal_.receive(value);
    return;
  }
  if (value == 0 && !sio_b_receive_ready_) {
    // A channel-reset/status-select write also acknowledges a character that
    // software consumed by polling instead of through the normal ISR path.
    terminal_interrupt_requested_ = false;
    sio_b_polling_ = true;
  }
  if (sio_b_register_ != 0) {
    if (sio_b_register_ == 5) {
      sio_b_dtr_ = (value & 0x80) != 0;
      if (!sio_b_dtr_) {
        terminal_interrupt_requested_ = false;
      }
    }
    sio_b_register_ = 0;
  } else if ((value & 0x07) != 0) {
    sio_b_register_ = value & 0x07;
  }
}

}  // namespace p2000c

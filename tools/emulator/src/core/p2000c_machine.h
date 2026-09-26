#ifndef P2000C_CORE_P2000C_MACHINE_H_
#define P2000C_CORE_P2000C_MACHINE_H_

#include <array>
#include <bitset>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <utility>
#include <vector>

#include "core/copower_board.h"
#include "core/raw_disk_image.h"
#include "core/terminal.h"

struct z80;

namespace p2000c {

/** Minimal mainboard model and integration boundary for P2000C devices. */
class P2000cMachine {
  private:
    static constexpr std::size_t kMemorySize = 64 * 1024;
    static constexpr std::size_t kIplRomSize = 4 * 1024;
    static constexpr std::uint64_t kHandshakeDelay = 4'000;
    static constexpr std::uint64_t kTimerPeriod = 4'000'000 / 60;

    struct DmaChannel {
        std::uint16_t address = 0;
        std::uint16_t count = 0;
    };

    struct TimedInterrupt {
        std::uint64_t due_cycle = 0;
        std::uint8_t vector = 0;
    };

  public:
    enum class StorageDevice { kFloppy, kHardDisk };
    enum class StorageOperation {
      kRead,
      kWrite,
      kSeek,
      kMotorStart,
      kMotorStop,
    };

    struct StorageActivity {
        StorageDevice device = StorageDevice::kFloppy;
        StorageOperation operation = StorageOperation::kRead;
        std::size_t drive = 0;
        int distance = 0;
        int duration_ms = 0;
    };

    using StorageActivityHandler =
        std::function<void(const StorageActivity& activity)>;

    /** Creates a reset mainboard with no firmware or media loaded. */
    P2000cMachine();

    /** Releases the integrated Z80 core. */
    ~P2000cMachine();
    P2000cMachine(const P2000cMachine&) = delete;
    P2000cMachine& operator=(const P2000cMachine&) = delete;

    /** Loads the 4 KiB mainboard IPL firmware. */
    bool load_ipl_rom(const std::filesystem::path& path, std::string* error);

    /** Loads and validates a 4 KiB mainboard IPL firmware byte sequence. */
    bool load_ipl_rom(std::span<const std::uint8_t> bytes, std::string* error);

    /** Mounts floppy drive A as a directly writable 640/800 KiB FLP image. */
    bool mount_floppy_a(const std::filesystem::path& path, std::string* error);

    /** Mounts floppy drive B as a directly writable 640/800 KiB FLP image. */
    bool mount_floppy_b(const std::filesystem::path& path, std::string* error);

    /** Mounts one of the two 10 MiB SASI hard-disk images. */
    bool mount_hard_disk(std::size_t drive, const std::filesystem::path& path,
                         std::string* error);

    /** Removes one of the two SASI hard-disk images. */
    bool unmount_hard_disk(std::size_t drive);

    /** Restores reset state, including the IPL ROM overlay at address zero. */
    void reset();

    /** Executes instructions until at least the requested T-states elapsed. */
    void run_for(std::uint64_t t_states);

    /** Returns whether a valid IPL ROM has been loaded. */
    bool has_ipl_rom() const { return has_ipl_rom_; }

    /** Returns the mounted floppy, if any. */
    const std::optional<RawDiskImage>& floppy_a() const {
      return floppy_drives_[0];
    }

    /** Returns the floppy mounted in drive B, if any. */
    const std::optional<RawDiskImage>& floppy_b() const {
      return floppy_drives_[1];
    }

    /** Returns either mounted physical SASI hard disk. */
    const std::optional<RawDiskImage>& hard_disk(std::size_t drive) const {
      return hard_disks_.at(drive);
    }

    /** Returns the cylinder most recently selected in a floppy drive. */
    std::uint8_t floppy_track(std::size_t drive) const {
      return fdc_tracks_.at(drive);
    }

    /** Returns the side most recently accessed in a floppy drive. */
    std::uint8_t floppy_side(std::size_t drive) const {
      return fdc_sides_.at(drive);
    }

    /** Returns the final SASI block touched by the most recent transfer. */
    std::size_t hard_disk_block(std::size_t drive) const {
      return sasi_blocks_.at(drive);
    }

    /** Returns the high-level serial terminal. */
    const Terminal& terminal() const { return terminal_; }
    Terminal& terminal() { return terminal_; }

    /** Queues a P2000C character as terminal keyboard input. */
    void queue_key(std::uint8_t value) { terminal_.queue_key(value); }

    /** Returns the main Z80 program counter for diagnostics. */
    std::uint16_t program_counter() const;

    /** Returns elapsed mainboard Z80 T-states since reset. */
    std::uint64_t cycles() const;

    /** Installs or removes the 512 KiB Philips CoPower board. */
    void set_copower_enabled(bool enabled) {
      copower_.set_enabled(enabled);
    }

    /** Returns whether the optional CoPower board is installed. */
    bool copower_enabled() const { return copower_.enabled(); }
    void set_copower_memory_kib(std::size_t kib) { copower_.set_memory_kib(kib); }

    /** Returns whether the CoPower 8088 stopped on an unsupported operation. */
    bool copower_faulted() const { return copower_.faulted(); }

    /** Returns the CoPower 8088 execution location for diagnostics. */
    std::pair<std::uint16_t, std::uint16_t> copower_program_counter() const {
      return {copower_.code_segment(), copower_.program_counter()};
    }

    /** Reads a byte through the current mainboard memory mapping. */
    std::uint8_t read_memory(std::uint16_t address) const;

    /** Writes a byte to mainboard RAM, including underneath the ROM overlay. */
    void write_memory(std::uint16_t address, std::uint8_t value);

    /** Returns distinct bytes written in each 256-byte page since reset. */
    const std::array<std::uint16_t, 256>& memory_page_write_counts() const {
      return memory_page_write_counts_;
    }

    /** Returns whether the 4 KiB IPL ROM currently covers low RAM. */
    bool ipl_rom_mapped() const { return memory_manager_ == 0; }

    /** Installs a callback for physical drive activity and presentation. */
    void set_storage_activity_handler(StorageActivityHandler handler) {
      storage_activity_handler_ = std::move(handler);
    }

    /** Enables or bypasses physical floppy latency without hiding activity. */
    void set_storage_delays_enabled(bool enabled) {
      storage_delays_enabled_ = enabled;
    }

    /** Returns whether floppy completion observes physical device latency. */
    bool storage_delays_enabled() const { return storage_delays_enabled_; }

  private:
    /** Adapts Z80 memory reads to the machine memory map. */
    static std::uint8_t cpu_read(void* context, std::uint16_t address);

    /** Adapts Z80 memory writes to mainboard RAM. */
    static void cpu_write(void* context, std::uint16_t address,
                          std::uint8_t value);

    /** Dispatches Z80 input instructions to mainboard devices. */
    static std::uint8_t cpu_port_in(z80* cpu, std::uint8_t port);

    /** Dispatches Z80 output instructions to mainboard devices. */
    static void cpu_port_out(z80* cpu, std::uint8_t port, std::uint8_t value);

    /** Selects the IPL-ROM overlay or the all-internal-RAM mapping. */
    void write_memory_manager(std::uint8_t value);

    /** Advances asynchronous devices and presents pending interrupts. */
    void update_devices();

    /** Adds a vectored interrupt, optionally after current floppy latency. */
    void request_interrupt(std::uint8_t vector,
                           bool apply_floppy_latency = true);

    /** Reads an Intel 8257 register. */
    std::uint8_t read_dma(std::uint8_t port);

    /** Writes an Intel 8257 register or mode byte. */
    void write_dma(std::uint8_t port, std::uint8_t value);

    /** Runs an enabled memory-to-terminal DMA channel. */
    void run_terminal_dma();

    /** Transfers disk data through DMA channel zero. */
    bool run_floppy_dma(std::span<const std::uint8_t> data,
                        bool apply_floppy_latency = true);

    /** Copies channel-zero memory into a device-write buffer. */
    std::optional<std::vector<std::uint8_t>> take_disk_dma(
        bool apply_floppy_latency = true);

    /** Returns the uPD765 main-status register. */
    std::uint8_t fdc_status() const;

    /** Accepts a byte written to the uPD765 data register. */
    void write_fdc(std::uint8_t value);

    /** Completes the currently collected uPD765 command. */
    void complete_fdc_command();

    /** Returns the byte count of a uPD765 command including its opcode. */
    static std::size_t fdc_command_size(std::uint8_t command);

    /** Handles a rising edge on the active-low uPD765 reset signal. */
    void release_fdc_reset();

    /** Returns the current SASI control-bus signals. */
    std::uint8_t read_sasi_control() const;

    /** Handles SASI SEL and RESET output signals. */
    void write_sasi_control(std::uint8_t value);

    /** Reads a SASI status or message byte. */
    std::uint8_t read_sasi_data();

    /** Accepts a SASI command byte. */
    void write_sasi_data(std::uint8_t value);

    /** Executes one complete six-byte SASI command. */
    void execute_sasi_command();

    /** Reads an SIO-B status or receive-data port. */
    std::uint8_t read_terminal_sio(std::uint8_t port);

    /** Writes an SIO-B control or transmit-data port. */
    void write_terminal_sio(std::uint8_t port, std::uint8_t value);

    /** Mounts one of the two supported floppy drives. */
    bool mount_floppy(std::size_t drive, const std::filesystem::path& path,
                      std::string* error);

    /** Returns a mounted floppy selected by a uPD765 unit number. */
    const RawDiskImage* floppy_drive(std::uint8_t drive) const;

    /** Reports an operation and optionally inserts floppy-device latency. */
    void begin_storage_activity(const StorageActivity& activity,
                                bool apply_latency = true);

    enum class SasiPhase {
      kBusFree,
      kCommand,
      kStatus,
      kMessage,
    };

    std::array<std::uint8_t, kMemorySize> ram_{};
    std::array<std::uint8_t, kIplRomSize> ipl_rom_{};
    std::bitset<kMemorySize> memory_written_{};
    std::array<std::uint16_t, 256> memory_page_write_counts_{};
    std::unique_ptr<z80> cpu_;
    CoPowerBoard copower_;
    std::array<std::optional<RawDiskImage>, 2> floppy_drives_;
    std::array<std::optional<RawDiskImage>, 2> hard_disks_;
    Terminal terminal_;
    std::array<DmaChannel, 4> dma_channels_{};
    std::deque<std::uint8_t> interrupt_queue_;
    std::deque<TimedInterrupt> timed_interrupts_;
    std::vector<std::uint8_t> fdc_command_;
    std::deque<std::uint8_t> fdc_result_;
    bool has_ipl_rom_ = false;
    std::uint8_t memory_manager_ = 0;
    bool dma_high_byte_ = false;
    bool dma_read_high_byte_ = false;
    bool handshake_started_ = false;
    bool terminal_interrupt_requested_ = false;
    bool sio_b_polling_ = false;
    bool sio_b_dtr_ = false;
    bool fdc_reset_released_ = false;
    bool fdc_sense_pending_ = false;
    std::uint8_t dma_mode_ = 0;
    std::uint8_t dma_status_ = 0;
    std::uint8_t fdc_output_ = 0;
    std::uint8_t fdc_sense_status_ = 0xc0;
    std::array<std::uint8_t, 2> fdc_tracks_{};
    std::array<std::uint8_t, 2> fdc_sides_{};
    std::uint8_t fdc_sense_track_ = 0;
    SasiPhase sasi_phase_ = SasiPhase::kBusFree;
    std::array<std::uint8_t, 6> sasi_command_{};
    std::size_t sasi_command_length_ = 0;
    std::uint8_t sasi_status_ = 0;
    std::array<std::size_t, 2> sasi_blocks_{};
    std::uint8_t sio_b_register_ = 0;
    std::uint8_t sio_b_receive_byte_ = 0;
    bool sio_b_receive_ready_ = false;
    std::uint64_t total_cycles_ = 0;
    std::uint64_t next_timer_cycle_ = kTimerPeriod;
    std::uint64_t storage_busy_until_ = 0;
    std::uint64_t fdc_ready_cycle_ = 0;
    StorageActivityHandler storage_activity_handler_;
    bool storage_delays_enabled_ = true;
};

}  // namespace p2000c

#endif  // P2000C_CORE_P2000C_MACHINE_H_

#ifndef P2000C_CORE_COPOWER_BOARD_H_
#define P2000C_CORE_COPOWER_BOARD_H_

#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

struct i8088;

namespace p2000c {

/** Philips CoPower 8088 coprocessor board with 512 KiB private RAM. */
class CoPowerBoard {
  public:
    static constexpr std::size_t kLocalMemorySize = 512 * 1024;

    using SharedRead = std::function<std::uint8_t(std::uint16_t address)>;
    using SharedWrite =
        std::function<void(std::uint16_t address, std::uint8_t value)>;
    using Z80Interrupt = std::function<void()>;

    CoPowerBoard(SharedRead shared_read, SharedWrite shared_write,
                 Z80Interrupt z80_interrupt);
    ~CoPowerBoard();
    CoPowerBoard(const CoPowerBoard&) = delete;
    CoPowerBoard& operator=(const CoPowerBoard&) = delete;

    /** Enables or removes the board and returns it to reset. */
    void set_enabled(bool enabled);
    /** Select physical RAM before boot; changing capacity clears its contents. */
    void set_memory_kib(std::size_t kib);
    bool enabled() const { return enabled_; }

    /** Applies a machine reset; board RAM is retained like mainboard RAM. */
    void reset();

    /** Runs the 5 MHz 8088 alongside the 4 MHz mainboard CPU. */
    void run_for(std::uint64_t z80_t_states);

    /** Supplies an 8088 interrupt vector through Z80 output port 30h. */
    void write_interrupt_vector(std::uint8_t vector);

    /** Handles reset/run/common-memory-lock control on Z80 port 31h. */
    void write_control(std::uint8_t value);

    bool held_in_reset() const { return held_in_reset_; }
    bool common_memory_locked() const { return common_memory_locked_; }
    bool faulted() const;
    std::uint16_t program_counter() const;
    std::uint16_t code_segment() const;

  private:
    static std::uint8_t cpu_read(void* context, std::uint32_t address);
    static void cpu_write(void* context, std::uint32_t address,
                          std::uint8_t value);
    static std::uint16_t cpu_port_in(void* context, std::uint16_t port,
                                    bool word);
    static void cpu_port_out(void* context, std::uint16_t port,
                             std::uint16_t value, bool word);

    std::uint8_t read(std::uint32_t address) const;
    void write(std::uint32_t address, std::uint8_t value);

    // Keep the board's 512 KiB RAM off the host call stack. Several machine
    // instances are deliberately created by the integration tests; embedding
    // this storage made those tests exceed the 1 MiB default Windows stack.
    std::vector<std::uint8_t> local_ram_ =
        std::vector<std::uint8_t>(kLocalMemorySize);
    SharedRead shared_read_;
    SharedWrite shared_write_;
    Z80Interrupt z80_interrupt_;
    i8088* cpu_ = nullptr;
    bool enabled_ = false;
    bool held_in_reset_ = true;
    bool common_memory_locked_ = false;
    std::uint64_t clock_accumulator_ = 0;
};

}  // namespace p2000c

#endif  // P2000C_CORE_COPOWER_BOARD_H_

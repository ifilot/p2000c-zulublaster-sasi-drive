#ifndef P2000C_THIRD_PARTY_BLINK16_I8088_H_
#define P2000C_THIRD_PARTY_BLINK16_I8088_H_

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint8_t (*i8088_read_callback)(void* context, uint32_t address);
typedef void (*i8088_write_callback)(void* context, uint32_t address,
                                    uint8_t value);
typedef uint16_t (*i8088_port_in_callback)(void* context, uint16_t port,
                                          bool word);
typedef void (*i8088_port_out_callback)(void* context, uint16_t port,
                                       uint16_t value, bool word);

typedef struct i8088_callbacks {
  void* context;
  i8088_read_callback read;
  i8088_write_callback write;
  i8088_port_in_callback port_in;
  i8088_port_out_callback port_out;
} i8088_callbacks;

typedef struct i8088 i8088;

i8088* i8088_create(i8088_callbacks callbacks);
void i8088_destroy(i8088* cpu);
void i8088_reset(i8088* cpu);
void i8088_step(i8088* cpu);
bool i8088_interrupt(i8088* cpu, uint8_t vector);
bool i8088_halted(const i8088* cpu);
bool i8088_faulted(const i8088* cpu);
uint16_t i8088_ip(const i8088* cpu);
uint16_t i8088_cs(const i8088* cpu);

#ifdef __cplusplus
}
#endif

#endif  // P2000C_THIRD_PARTY_BLINK16_I8088_H_

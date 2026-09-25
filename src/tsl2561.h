#include <stdint.h>

// TSL2561 default I2C address (ADDR connected to GND)
#define TSL2561_ADDR 0x39

// Define I2C port and pins (GP2 and GP3 use i2c1)
#define I2C_PORT_tsl i2c1
#define I2C_SDA_tsl 2
#define I2C_SCL_tsl 3

// TSL2561 Register Commands
#define TSL2561_CMD 0x80
#define TSL2561_REG_CONTROL 0x00
#define TSL2561_REG_TIMING 0x01
#define TSL2561_REG_DATA0LOW 0x0C

// Power commands
#define TSL2561_POWERON 0x03

void tsl2561_write_register(uint8_t reg, uint8_t value);
uint16_t tsl2561_read16(uint8_t reg);

#include "tsl2561.h"
#include <stdint.h>
#include <stdbool.h>
#include "hardware/i2c.h"

void tsl2561_write_register(uint8_t reg, uint8_t value) {
    uint8_t buf[2];
    buf[0] = TSL2561_CMD | reg;
    buf[1] = value;
    i2c_write_blocking(I2C_PORT_tsl, TSL2561_ADDR, buf, 2, false);
}

uint16_t tsl2561_read16(uint8_t reg) {
    uint8_t val[2] = {0};
    uint8_t cmd = TSL2561_CMD | reg;
    
    // Write register address, then read 2 bytes back
    i2c_write_blocking(I2C_PORT_tsl, TSL2561_ADDR, &cmd, 1, true);
    i2c_read_blocking(I2C_PORT_tsl, TSL2561_ADDR, val, 2, false);
    
    // TSL2561 sends low byte first, then high byte
    return (val[1] << 8) | val[0];
}
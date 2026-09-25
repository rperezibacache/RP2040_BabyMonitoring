
#include <stdint.h>
#include <stdlib.h>
#include "hardware/i2c.h"
#include "pico/stdlib.h"

// Define I2C port and pins (GP4 and GP5 use i2c0)
#define I2C_PORT_ENSHT i2c0
#define I2C_SDA_ENSHT 4
#define I2C_SCL_ENSHT 5

// Sensor I2C Target Addresses
#define AHT21_ADDR        0x38
#define ENS160_ADDR        0x53  // Try 0x52 if 0x53 doesn't respond

// ENS160 Registers & Commands
#define ENS160_REG_OPMODE  0x10
#define ENS160_REG_DATA_AQI 0x21
#define ENS160_REG_DATA_TVOC 0x22
#define ENS160_REG_DATA_ECO2 0x24

#define ENS160_OPMODE_RESET 0xF0
#define ENS160_OPMODE_IDLE  0x01
#define ENS160_OPMODE_STD   0x02 // Standard operating mode

void i2c_write_reg(uint8_t addr, uint8_t reg, uint8_t value);
void i2c_read_regs(uint8_t addr, uint8_t reg, uint8_t *buf, size_t len);
void aht21_init();
void aht21_read(float *temp, float *humidity);
void ens160_init();
void ens160_read(uint8_t *aqi, uint16_t *tvoc, uint16_t *eco2);


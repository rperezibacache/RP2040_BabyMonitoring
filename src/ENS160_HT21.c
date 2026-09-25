#include <stdint.h>
#include <stdbool.h>
#include "hardware/i2c.h"
#include "pico/stdlib.h"
#include "ENS160_HT21.h"

// Helper to write a 1-byte value to a sensor register
void i2c_write_reg(uint8_t addr, uint8_t reg, uint8_t value) {
    uint8_t buf[2] = {reg, value};
    i2c_write_blocking(I2C_PORT_ENSHT, addr, buf, 2, false);
}

// Helper to read multiple bytes from a starting register
void i2c_read_regs(uint8_t addr, uint8_t reg, uint8_t *buf, size_t len) {
    i2c_write_blocking(I2C_PORT_ENSHT, addr, &reg, 1, true);
    i2c_read_blocking(I2C_PORT_ENSHT, addr, buf, len, false);
}

// Initialize AHT21 Climate Sensor
void aht21_init() {
    sleep_ms(100); // Wait for sensor to boot up physically
    uint8_t status = 0;
    i2c_read_blocking(I2C_PORT_ENSHT, AHT21_ADDR, &status, 1, false);
    
    // If the calibration status bit (0x08) is not set, initialize it
    if ((status & 0x08) == 0) {
        uint8_t init_cmd[3] = {0xBE, 0x08, 0x00};
        i2c_write_blocking(I2C_PORT_ENSHT, AHT21_ADDR, init_cmd, 3, false);
        sleep_ms(10);
    }
}

// Read Temperature and Humidity from AHT21
void aht21_read(float *temp, float *humidity) {
    // Send trigger measurement command
    uint8_t trigger_cmd[3] = {0xAC, 0x33, 0x00};
    i2c_write_blocking(I2C_PORT_ENSHT, AHT21_ADDR, trigger_cmd, 3, false);
    
    // Wait for conversion completion (requires 80ms minimum)
    sleep_ms(85);
    
    uint8_t data[7];
    i2c_read_blocking(I2C_PORT_ENSHT, AHT21_ADDR, data, 7, false);
    
    // Parse raw 20-bit values from the data frame
    uint32_t raw_humidity = (((uint32_t)data[1]) << 12) | (((uint32_t)data[2]) << 4) | ((data[3] & 0xF0) >> 4);
    uint32_t raw_temp = (((uint32_t)(data[3] & 0x0F)) << 16) | (((uint32_t)data[4]) << 8) | data[5];
    
    // Convert mathematical values into real units
    *humidity = ((float)raw_humidity / 1048576.0f) * 100.0f;
    *temp = ((float)raw_temp / 1048576.0f) * 200.0f - 50.0f;
}

// Initialize ENS160 Multi-Gas Sensor
void ens160_init() {
    i2c_write_reg(ENS160_ADDR, ENS160_REG_OPMODE, ENS160_OPMODE_RESET);
    sleep_ms(50);
    i2c_write_reg(ENS160_ADDR, ENS160_REG_OPMODE, ENS160_OPMODE_STD);
    sleep_ms(20);
}

// Read Gas Metrics from ENS160
void ens160_read(uint8_t *aqi, uint16_t *tvoc, uint16_t *eco2) {
    uint8_t buf[2];
    
    // Read Air Quality Index (1 byte)
    i2c_read_regs(ENS160_ADDR, ENS160_REG_DATA_AQI, aqi, 1);
    
    // Read Total Volatile Organic Compounds (2 bytes, Little Endian)
    i2c_read_regs(ENS160_ADDR, ENS160_REG_DATA_TVOC, buf, 2);
    *tvoc = buf[0] | (buf[1] << 8);
    
    // Read Equivalent CO2 (2 bytes, Little Endian)
    i2c_read_regs(ENS160_ADDR, ENS160_REG_DATA_ECO2, buf, 2);
    *eco2 = buf[0] | (buf[1] << 8);
}
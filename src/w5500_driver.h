#ifndef W5500_DRIVER_H
#define W5500_DRIVER_H

#include <stdint.h>
#include <stdbool.h>

/* W5500 block select bits for control byte */
#define W5500_BSB_COMMON    0x00    /* Common registers */
#define W5500_BSB_S0_REG    0x01    /* Socket 0 registers */
#define W5500_BSB_S0_TX     0x02    /* Socket 0 TX buffer */
#define W5500_BSB_S0_RX     0x03    /* Socket 0 RX buffer */

/* Initialize W5500 SPI and network config */
bool w5500_init(void);

/* Hardware reset via RST pin */
void w5500_reset(void);

/* Register access (single byte) */
uint8_t w5500_read_reg(uint16_t addr, uint8_t bsb);
void    w5500_write_reg(uint16_t addr, uint8_t bsb, uint8_t val);

/* Register access (multi-byte burst) */
void w5500_read_regs(uint16_t addr, uint8_t bsb, uint8_t *buf, uint16_t len);
void w5500_write_regs(uint16_t addr, uint8_t bsb, const uint8_t *buf, uint16_t len);

/* Check Ethernet link status */
bool w5500_is_link_up(void);

#endif
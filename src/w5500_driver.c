#include "w5500_driver.h"
#include "config.h"
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/gpio.h"
#include <stdio.h>

/* W5500 control byte layout:
 *  Bit 7-3: BSB (Block Select Bits)
 *  Bit 2:   RWB (0=Read, 1=Write)
 *  Bit 1-0: OM (00=Variable data length) */
#define W5500_OP_READ       0x00
#define W5500_OP_WRITE      0x04

/* Common register map */
#define W5500_MR            0x0000
#define W5500_GAR           0x0001
#define W5500_SUBR          0x0005
#define W5500_SHAR          0x0009
#define W5500_SIPR          0x000F
#define W5500_PHYCFGR       0x002E
#define W5500_VERSIONR      0x0039

static inline void cs_select(void)
{
    gpio_put(W5500_CS_PIN, 0);
    sleep_us(1);
}

static inline void cs_deselect(void)
{
    sleep_us(1);
    gpio_put(W5500_CS_PIN, 1);
}

static uint8_t w5500_xfer(uint8_t tx)
{
    uint8_t rx;
    spi_write_read_blocking(W5500_SPI_PORT, &tx, &rx, 1);
    return rx;
}

static uint8_t make_ctrl(uint8_t bsb, bool is_write)
{
    return (bsb << 3) | (is_write ? W5500_OP_WRITE : W5500_OP_READ);
}

uint8_t w5500_read_reg(uint16_t addr, uint8_t bsb)
{
    uint8_t tx[4] = {
        (addr >> 8) & 0xFF,
        addr & 0xFF,
        make_ctrl(bsb, false),
        0x00
    };
    uint8_t rx[4];
    cs_select();
    spi_write_read_blocking(W5500_SPI_PORT, tx, rx, 4);
    cs_deselect();
    return rx[3];
}

void w5500_write_reg(uint16_t addr, uint8_t bsb, uint8_t val)
{
    uint8_t tx[4] = {
        (addr >> 8) & 0xFF,
        addr & 0xFF,
        make_ctrl(bsb, true),
        val
    };
    uint8_t rx[4];
    cs_select();
    spi_write_read_blocking(W5500_SPI_PORT, tx, rx, 4);
    cs_deselect();
    (void)rx; /* suppress unused warning */
}

void w5500_read_regs(uint16_t addr, uint8_t bsb, uint8_t *buf, uint16_t len)
{
    cs_select();
    w5500_xfer((addr >> 8) & 0xFF);
    w5500_xfer(addr & 0xFF);
    w5500_xfer(make_ctrl(bsb, false));
    for (uint16_t i = 0; i < len; i++) {
        buf[i] = w5500_xfer(0x00);
    }
    cs_deselect();
}

void w5500_write_regs(uint16_t addr, uint8_t bsb, const uint8_t *buf, uint16_t len)
{
    cs_select();
    w5500_xfer((addr >> 8) & 0xFF);
    w5500_xfer(addr & 0xFF);
    w5500_xfer(make_ctrl(bsb, true));
    for (uint16_t i = 0; i < len; i++) {
        w5500_xfer(buf[i]);
    }
    cs_deselect();
}

void w5500_reset(void)
{
    gpio_put(W5500_RST_PIN, 0);
    sleep_ms(10);
    gpio_put(W5500_RST_PIN, 1);
    sleep_ms(10);
}

bool w5500_init(void)
{
    /* Initialize SPI1 at 1 MHz (safe for initialization) */
    spi_init(W5500_SPI_PORT, 1000 * 1000);
    spi_set_format(W5500_SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);

    /* Configure GPIOs */
    gpio_set_function(W5500_SCK_PIN, GPIO_FUNC_SPI);
    gpio_set_function(W5500_MOSI_PIN, GPIO_FUNC_SPI);
    gpio_set_function(W5500_MISO_PIN, GPIO_FUNC_SPI);

    gpio_init(W5500_CS_PIN);
    gpio_set_dir(W5500_CS_PIN, GPIO_OUT);
    gpio_put(W5500_CS_PIN, 1);

    gpio_init(W5500_RST_PIN);
    gpio_set_dir(W5500_RST_PIN, GPIO_OUT);
    gpio_put(W5500_RST_PIN, 1);

    gpio_init(W5500_INT_PIN);
    gpio_set_dir(W5500_INT_PIN, GPIO_IN);
    gpio_pull_up(W5500_INT_PIN);

    /* Hardware reset */
    w5500_reset();

    /* Verify chip version (W5500 should return 0x04) */
    uint8_t version = w5500_read_reg(W5500_VERSIONR, W5500_BSB_COMMON);
    if (version != 0x04) {
        printf("W5500: Warning - version 0x%02X (expected 0x04)\r\n", version);
    }

    /* Set MAC, IP, subnet, gateway */
    const uint8_t mac[] = W5500_MAC_ADDR;
    w5500_write_regs(W5500_SHAR, W5500_BSB_COMMON, mac, 6);

    const uint8_t ip[] = W5500_IP_ADDR;
    w5500_write_regs(W5500_SIPR, W5500_BSB_COMMON, ip, 4);

    const uint8_t subnet[] = W5500_SUBNET;
    w5500_write_regs(W5500_SUBR, W5500_BSB_COMMON, subnet, 4);

    const uint8_t gateway[] = W5500_GATEWAY;
    w5500_write_regs(W5500_GAR, W5500_BSB_COMMON, gateway, 4);

    /* PHY auto-negotiation, all capable */
    w5500_write_reg(W5500_PHYCFGR, W5500_BSB_COMMON, 0xD8);
    sleep_ms(100);

    return w5500_is_link_up();
}

bool w5500_is_link_up(void)
{
    uint8_t phycfg = w5500_read_reg(W5500_PHYCFGR, W5500_BSB_COMMON);
    return (phycfg & 0x01) != 0;
}
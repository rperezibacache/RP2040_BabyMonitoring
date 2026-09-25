#ifndef CONFIG_H
#define CONFIG_H

/*
 * Hardware pin mapping
 * 
 * LCD 2004A-1 (HD44780 compatible) - 4-bit parallel mode
 * Based on schematic: DMC204LCD via EXP1 header
 * 
 * EXP1 Header -> RP2040 GPIO mapping:
 *   EXP1 Pin 3 (LCDE)  -> GPIO 3  (Enable)
 *   EXP1 Pin 5 (LCD4)  -> GPIO 4  (Data bit 4)
 *   EXP1 Pin 6 (LCD5)  -> GPIO 5  (Data bit 5)
 *   EXP1 Pin 7 (LCD6)  -> GPIO 6  (Data bit 6)
 *   EXP1 Pin 8 (LCD7)  -> GPIO 7  (Data bit 7)
 * 
 * Note: LCDRS is not clearly routed through EXP1 in the schematic.
 * It is assigned to GPIO 2 below. Adjust if your hardware differs.
 * 
 * R/W (LCD pin 5) is grounded in schematic -> write-only mode.
 * VLCD (LCD pin 3) uses 10K potentiometer R1 for contrast.
 * Backlight (pin 15/16) uses RLED resistor to VCC -> always on.
 */

#define LCD_RS_PIN          6   /* Register Select - shifted from 2 */
#define LCD_E_PIN           7   /* Enable - shifted from 3 */
#define LCD_D4_PIN          8   /* Data bit 4 - shifted from 4 */
#define LCD_D5_PIN          9   /* Data bit 5 - shifted from 5 */
#define LCD_D6_PIN          10  /* Data bit 6 - shifted from 6 */
#define LCD_D7_PIN          11  /* Data bit 7 - shifted from 7 */


/* Optional backlight control GPIO (-1 if hardwired as in schematic) */
#define LCD_BL_PIN          (-1)

/*
 * WIZnet W5500 Ethernet - SPI1 interface
 * Standard SPI mode 0, MSB first
 */
#define W5500_SPI_PORT      spi1
#define W5500_SCK_PIN       10
#define W5500_MOSI_PIN      11
#define W5500_MISO_PIN      12
#define W5500_CS_PIN        13
#define W5500_RST_PIN       14
#define W5500_INT_PIN       15

/* Default network configuration */
#define W5500_MAC_ADDR      {0x00, 0x08, 0xDC, 0x11, 0x22, 0x33}
#define W5500_IP_ADDR       {192, 168, 1, 100}
#define W5500_SUBNET        {255, 255, 255, 0}
#define W5500_GATEWAY       {192, 168, 1, 1}

/* FreeRTOS task configuration */
#define LCD_TASK_PRIORITY       (tskIDLE_PRIORITY + 2)
#define LCD_TASK_STACK_SIZE     (configMINIMAL_STACK_SIZE * 2)
#define LCD_UPDATE_INTERVAL_MS  200

#define W5500_TASK_PRIORITY     (tskIDLE_PRIORITY + 1)
#define W5500_TASK_STACK_SIZE   (configMINIMAL_STACK_SIZE * 2)


typedef struct {
    float temperature;
    float humidity;
    uint8_t aqi;
    uint16_t tvoc;
    uint16_t eco2;
    uint16_t broadband;
    uint16_t ir;
} sensor_data_t;

#endif
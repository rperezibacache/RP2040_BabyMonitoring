#include "lcd_2004a.h"
#include "config.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "FreeRTOS.h"
#include "task.h"

/* HD44780 timing (microseconds) */
#define LCD_PULSE_US        2
#define LCD_CMD_DELAY_US    50
#define LCD_CLEAR_DELAY_US  2000
#define LCD_INIT_DELAY_MS   10


/* Safe environment delay helper */
static void safe_delay_ms(uint32_t ms) {
    if (xTaskGetSchedulerState() == taskSCHEDULER_NOT_STARTED) {
        // Scheduler is offline; use raw hardware timers
        sleep_ms(ms);
    } else {
        // Scheduler is active; use safe operating system delay
        vTaskDelay(pdMS_TO_TICKS(ms));
    }
}
/* Pulse the Enable line */
static inline void lcd_pulse_enable(void)
{
    gpio_put(LCD_E_PIN, 1);
    sleep_us(LCD_PULSE_US);
    gpio_put(LCD_E_PIN, 0);
    sleep_us(LCD_PULSE_US);
}

/* Send a 4-bit nibble to D7-D4 */
static void lcd_send_nibble(uint8_t nibble)
{
    gpio_put(LCD_D4_PIN, (nibble >> 0) & 1);
    gpio_put(LCD_D5_PIN, (nibble >> 1) & 1);
    gpio_put(LCD_D6_PIN, (nibble >> 2) & 1);
    gpio_put(LCD_D7_PIN, (nibble >> 3) & 1);
    lcd_pulse_enable();
}

/* Send full byte in 4-bit mode: high nibble first, then low nibble */
static void lcd_send_byte(uint8_t byte, bool is_data)
{
    gpio_put(LCD_RS_PIN, is_data ? 1 : 0);
    sleep_us(1);

    lcd_send_nibble(byte >> 4);
    sleep_us(LCD_CMD_DELAY_US);

    lcd_send_nibble(byte & 0x0F);
    sleep_us(LCD_CMD_DELAY_US);
}

/* Send command byte */
static void lcd_command(uint8_t cmd)
{
    lcd_send_byte(cmd, false);
    if (cmd == LCD_CMD_CLEAR_DISPLAY || cmd == LCD_CMD_RETURN_HOME) {
        sleep_us(LCD_CLEAR_DELAY_US);
    } else {
        sleep_us(LCD_CMD_DELAY_US);
    }
}

/* Send data byte */
static void lcd_data(uint8_t data)
{
    lcd_send_byte(data, true);
    sleep_us(LCD_CMD_DELAY_US);
}

void lcd_init(void)
{
    /* Initialize and direct the new pin allocations */
    gpio_init(LCD_RS_PIN);
    gpio_init(LCD_E_PIN);
    gpio_init(LCD_D4_PIN);
    gpio_init(LCD_D5_PIN);
    gpio_init(LCD_D6_PIN);
    gpio_init(LCD_D7_PIN);

    gpio_set_dir(LCD_RS_PIN, GPIO_OUT);
    gpio_set_dir(LCD_E_PIN, GPIO_OUT);
    gpio_set_dir(LCD_D4_PIN, GPIO_OUT);
    gpio_set_dir(LCD_D5_PIN, GPIO_OUT);
    gpio_set_dir(LCD_D6_PIN, GPIO_OUT);
    gpio_set_dir(LCD_D7_PIN, GPIO_OUT);

    gpio_put(LCD_RS_PIN, 0);
    gpio_put(LCD_E_PIN, 0);
    gpio_put(LCD_D4_PIN, 0);
    gpio_put(LCD_D5_PIN, 0);
    gpio_put(LCD_D6_PIN, 0);
    gpio_put(LCD_D7_PIN, 0);

#if LCD_BL_PIN >= 0
    gpio_init(LCD_BL_PIN);
    gpio_set_dir(LCD_BL_PIN, GPIO_OUT);
    gpio_put(LCD_BL_PIN, 1);
#endif

    /* Hardware initialization sequence - Significantly slowed down for safety */
    safe_delay_ms(100);                 /* Wait for Vcc to settle completely */

    lcd_send_nibble(0x03);              /* First attempt at 8-bit mode */
    safe_delay_ms(15);                  /* Increased to 15ms */

    lcd_send_nibble(0x03);              /* Second attempt */
    safe_delay_ms(5);                   /* Increased to 5ms */

    lcd_send_nibble(0x03);              /* Third attempt */
    safe_delay_ms(5);

    lcd_send_nibble(0x02);              /* Force transition to 4-bit mode */
    safe_delay_ms(5);

    /* Apply geometry and activate panel */
    lcd_command(LCD_CMD_FUNCTION_SET | LCD_4BIT_MODE | LCD_2LINE_MODE | LCD_5x8_FONT);
    safe_delay_ms(2);
    
    lcd_command(LCD_CMD_DISPLAY_CTRL | LCD_DISPLAY_OFF | LCD_CURSOR_OFF | LCD_BLINK_OFF);
    safe_delay_ms(2);
    
    lcd_clear();
    safe_delay_ms(5);
    
    /* CRITICAL FIX: Force Left-to-Right text entry and TURN OFF shift displacement */
    lcd_command(LCD_CMD_ENTRY_MODE | LCD_ENTRY_INCREMENT | LCD_ENTRY_SHIFT_OFF);
    safe_delay_ms(5);

    /* Turn display back on with settings locked in */
    lcd_command(LCD_CMD_DISPLAY_CTRL | LCD_DISPLAY_ON | LCD_CURSOR_OFF | LCD_BLINK_OFF);
    safe_delay_ms(5);

}


void lcd_clear(void)
{
    lcd_command(LCD_CMD_CLEAR_DISPLAY);
}

void lcd_home(void)
{
    lcd_command(LCD_CMD_RETURN_HOME);
}

void lcd_set_cursor(uint8_t col, uint8_t row)
{
    if (row >= LCD_ROWS) row = LCD_ROWS - 1;
    if (col >= LCD_COLS) col = LCD_COLS - 1;

    static const uint8_t row_addrs[LCD_ROWS] = {
        LCD_ROW0_ADDR, LCD_ROW1_ADDR, LCD_ROW2_ADDR, LCD_ROW3_ADDR
    };

    lcd_command(LCD_CMD_SET_DDRAM_ADDR | (row_addrs[row] + col));
}

void lcd_write_char(char c)
{
    lcd_data((uint8_t)c);
}

void lcd_write_string(const char *str)
{
    while (*str) {
        lcd_write_char(*str++);
    }
}

void lcd_write_string_ln(uint8_t row, const char *str)
{
    lcd_set_cursor(0, row);
    lcd_write_string(str);
}

void lcd_display_control(bool display_on, bool cursor_on, bool blink_on)
{
    uint8_t cmd = LCD_CMD_DISPLAY_CTRL;
    if (display_on) cmd |= LCD_DISPLAY_ON;
    if (cursor_on)  cmd |= LCD_CURSOR_ON;
    if (blink_on)   cmd |= LCD_BLINK_ON;
    lcd_command(cmd);
}

void lcd_backlight(bool on)
{
#if LCD_BL_PIN >= 0
    gpio_put(LCD_BL_PIN, on ? 1 : 0);
#endif
}
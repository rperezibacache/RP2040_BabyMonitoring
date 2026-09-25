#ifndef LCD_2004A_H
#define LCD_2004A_H

#include <stdint.h>
#include <stdbool.h>

/* LCD geometry */
#define LCD_COLS    20
#define LCD_ROWS    4

/* DDRAM row start addresses for 20x4 HD44780 displays */
#define LCD_ROW0_ADDR   0x00
#define LCD_ROW1_ADDR   0x40
#define LCD_ROW2_ADDR   0x14
#define LCD_ROW3_ADDR   0x54

/* HD44780 instruction set */
#define LCD_CMD_CLEAR_DISPLAY   0x01
#define LCD_CMD_RETURN_HOME     0x02
#define LCD_CMD_ENTRY_MODE      0x04
#define LCD_CMD_DISPLAY_CTRL    0x08
#define LCD_CMD_CURSOR_SHIFT    0x10
#define LCD_CMD_FUNCTION_SET    0x20
#define LCD_CMD_SET_DDRAM_ADDR  0x80

/* Entry mode flags */
#define LCD_ENTRY_INCREMENT     0x02
#define LCD_ENTRY_DECREMENT     0x00
#define LCD_ENTRY_SHIFT_ON      0x01
#define LCD_ENTRY_SHIFT_OFF     0x00

/* Display control flags */
#define LCD_DISPLAY_ON          0x04
#define LCD_DISPLAY_OFF         0x00
#define LCD_CURSOR_ON           0x02
#define LCD_CURSOR_OFF          0x00
#define LCD_BLINK_ON            0x01
#define LCD_BLINK_OFF           0x00

/* Function set flags */
#define LCD_8BIT_MODE           0x10
#define LCD_4BIT_MODE           0x00
#define LCD_2LINE_MODE          0x08
#define LCD_1LINE_MODE          0x00
#define LCD_5x10_FONT           0x04
#define LCD_5x8_FONT            0x00

/* Initialize LCD in 4-bit mode */
void lcd_init(void);

/* Clear display and return cursor home */
void lcd_clear(void);
void lcd_home(void);

/* Set cursor position (col 0-19, row 0-3) */
void lcd_set_cursor(uint8_t col, uint8_t row);

/* Write single character or null-terminated string */
void lcd_write_char(char c);
void lcd_write_string(const char *str);

/* Write string starting at column 0 of specified row */
void lcd_write_string_ln(uint8_t row, const char *str);

/* Display/cursor/blink control */
void lcd_display_control(bool display_on, bool cursor_on, bool blink_on);

/* Backlight control (if GPIO configured) */
void lcd_backlight(bool on);

#endif
#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "FreeRTOS.h"
#include "task.h"
#include "lcd_2004a.h"
#include "w5500_driver.h"
#include "config.h"
#include "task.h"
#include "hardware/gpio.h"
#include "tsl2561.h"
#include "hardware/i2c.h"
#include "ENS160_HT21.h"

/* Scrolling text configuration */
#define SCROLL_TEXT     "     Hello World     "   /* 21 chars with padding */
#define SCROLL_LEN      21
#define DISPLAY_WIDTH   20

// tsl 2561 sensor configuration



static char scroll_buffer[SCROLL_LEN * 2];
static sensor_data_t g_sensor_values = {0};
/* LCD scrolling task */
// static void vLCDTask(void *pvParameters)
// {
//     (void)pvParameters;
//     /* Double the text for seamless circular scrolling */
//     memcpy(scroll_buffer, SCROLL_TEXT, SCROLL_LEN);
//     memcpy(scroll_buffer + SCROLL_LEN, SCROLL_TEXT, SCROLL_LEN);

//     uint8_t offset = 0;
//     char display_line[DISPLAY_WIDTH + 1];

//     /* Static info on lines 1-3 */
//     lcd_write_string_ln(1, "  RP2040 + W5500   ");
//     lcd_write_string_ln(2, "   FreeRTOS SMP    ");
//     lcd_write_string_ln(3, "  4-Bit Parallel   ");

//     for (;;) {
//         /* Extract 20-character window */
//         for (int i = 0; i < DISPLAY_WIDTH; i++) {
//             display_line[i] = scroll_buffer[offset + i];
//         }
//         display_line[DISPLAY_WIDTH] = '\0';

//         /* Update top line with scrolling text */
//         lcd_set_cursor(0, 0);
//         lcd_write_string(display_line);

//         /* Advance and wrap */
//         offset++;
//         if (offset >= SCROLL_LEN) {
//             offset = 0;
//         }

//         vTaskDelay(pdMS_TO_TICKS(LCD_UPDATE_INTERVAL_MS));
//     }
// }

void vLCDTask(void *pvParameters) {
    (void)pvParameters;

    char line_buf[21]; // 20 columns + 1 null terminator
    sensor_data_t local_copy;

    // Flush out initialization artifacts with a safe critical section wipe
    // taskENTER_CRITICAL();
    lcd_clear();
    // taskEXIT_CRITICAL();
    vTaskDelay(pdMS_TO_TICKS(100));

    for (;;) {
        // 1. Grab a snapshot copy of the data from the mutex
        // if (xSemaphoreTake(g_sensor_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
            local_copy = g_sensor_values;
        //     xSemaphoreGive(g_sensor_mutex);
        // }

        // 2. Format and render each line carefully within 20 character limits
        // taskENTER_CRITICAL();

        // Line 0: Temperature and Relative Humidity
        snprintf(line_buf, sizeof(line_buf), "T:%4.1f*C  H:%4.1f%%   ", 
                 local_copy.temperature, local_copy.humidity);
        lcd_write_string_ln(0, line_buf);

        // Line 1: Equivalent CO2 tracking
        snprintf(line_buf, sizeof(line_buf), "eCO2: %4u ppm      ", 
                 local_copy.eco2);
        lcd_write_string_ln(1, line_buf);

        // Line 2: Air Quality Index (AQI) & Organic Compunds
        snprintf(line_buf, sizeof(line_buf), "AQI:%d  TVOC:%4u ppb ", 
                 local_copy.aqi, local_copy.tvoc);
        lcd_write_string_ln(2, line_buf);

        // Line 3: Light Levels (Broadband Spectrum Data)
        snprintf(line_buf, sizeof(line_buf), "Lux Light: %5u     ", 
                 local_copy.broadband);
        lcd_write_string_ln(3, line_buf);

        // taskEXIT_CRITICAL();

        // Refresh panel text cleanly every 1 second
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}


/* W5500 Ethernet monitoring task */
static void vW5500Task(void *pvParameters)
{
    (void)pvParameters;

    bool link_up = w5500_init();

    printf("W5500 init: Link %s\r\n", link_up ? "UP" : "DOWN");

    bool last_link = link_up;

    for (;;) {
        bool current = w5500_is_link_up();
        if (current != last_link) {
            last_link = current;
            printf("W5500: Link %s\r\n", current ? "UP" : "DOWN");
        }
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

// main task 

void vTaskFunction( void * pvParameters )
{
    const uint LED_PIN = PICO_DEFAULT_LED_PIN;
    bool LED_state = false;
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);
    // tsl 2561 

    // ======== set interruption configuration =========== //
    TickType_t xLastWakeTime;
    const TickType_t xFrequency = pdMS_TO_TICKS(1000);

    // Initialise the xLastWakeTime variable with the current time.
    xLastWakeTime = xTaskGetTickCount();
    for( ;; )
    {
    //  ========= Wait for the next cycle THE INTERRUPTION CONDITION ==================== //
    vTaskDelayUntil( &xLastWakeTime, xFrequency );
    // Lux sensor reading tsl2561
    uint16_t broadband = tsl2561_read16(TSL2561_REG_DATA0LOW);
    uint16_t ir = tsl2561_read16(TSL2561_REG_DATA0LOW + 2);
    
    //  ===== ENS160 and AHT21 sensor readings ===== //
    float temperature = 0.0f;
    float humidity = 0.0f;
    uint8_t aqi = 0;
    uint16_t tvoc = 0;
    uint16_t eco2 = 0;
    // Collect samples from both targets
    aht21_read(&temperature, &humidity);
    ens160_read(&aqi, &tvoc, &eco2);

    // Store sensor values
    g_sensor_values.temperature = temperature;
    g_sensor_values.humidity = humidity;
    g_sensor_values.aqi = aqi;
    g_sensor_values.tvoc = tvoc;
    g_sensor_values.eco2 = eco2;
    g_sensor_values.broadband = broadband;
    g_sensor_values.ir = ir;

    // Output results to serial bus
    printf("\n--- Sensor Readings ---\n");
    printf("Temperature: %.2f °C | Humidity: %.2f %%\n", temperature, humidity);
    printf("AQI: %d (1-5) | TVOC: %d ppb | eCO2: %d ppm\n", aqi, tvoc, eco2);
    printf("Broadband (Visible + IR): %d | Infrared: %d\n", broadband, ir);
    //pwm_set_chan_level(slice_pwm_FAN_PUMP, PWM_CHAN_A, 1300); //
    //pwm_set_chan_level(slice_pwm_FAN_PUMP, PWM_CHAN_B, 1300); //

    LED_state = gpio_get_out_level(LED_PIN);
    gpio_put(LED_PIN, !LED_state);
    }
}



int main(void)
{
    stdio_init_all();
    sleep_ms(1000);     /* Wait for USB CDC serial */

    printf("\r\n========================================\r\n");
    printf(" RP2040 LCD2004A + W5500 FreeRTOS\r\n");
    printf("========================================\r\n");

    /* Initialize LCD before scheduler starts */
    lcd_init();
    lcd_clear();
    lcd_write_string_ln(0, "   Initializing...  ");
    lcd_write_string_ln(1, "  RP2040 + W5500   ");
    lcd_write_string_ln(2, "   FreeRTOS SMP    ");
    lcd_write_string_ln(3, "  4-Bit Parallel   ");
    sleep_ms(800);

    // =====  Initialize I2C1 at 100 kHz for the tsl 2561 sensor
    i2c_init(I2C_PORT_tsl, 100 * 1000);
    gpio_set_function(I2C_SDA_tsl, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_tsl, GPIO_FUNC_I2C);
    // Enable internal pull-ups (external resistors are still recommended)
    gpio_pull_up(I2C_SDA_tsl);
    gpio_pull_up(I2C_SCL_tsl);
    // Power on the TSL2561 sensor
    tsl2561_write_register(TSL2561_REG_CONTROL, TSL2561_POWERON);
    // ===== 
    // Initialize I2C0 at 100 kHz ENS160 and AHT21 sensors
    i2c_init(I2C_PORT_ENSHT, 100 * 1000);
    gpio_set_function(I2C_SDA_ENSHT, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL_ENSHT, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA_ENSHT);
    gpio_pull_up(I2C_SCL_ENSHT);
    //
    printf("Initializing ENS160 and AHT21 sensors...\n");
    aht21_init();
    ens160_init();
    printf("Sensors initialized successfully.\n");

    /* Create application tasks */
    xTaskCreate(vLCDTask, "LCD", LCD_TASK_STACK_SIZE, NULL,
                LCD_TASK_PRIORITY, NULL);
    // xTaskCreate(vW5500Task, "W5500", W5500_TASK_STACK_SIZE, NULL,
                // W5500_TASK_PRIORITY, NULL);
    xTaskCreate(vTaskFunction, "ISR_Task", 256, NULL, 1, NULL);
    printf("Starting FreeRTOS scheduler...\r\n");
    vTaskStartScheduler();

    /* Should never reach here */
    for (;;) {
        tight_loop_contents();
    }

    return 0;
}

void vApplicationStackOverflowHook(TaskHandle_t xTask, char *pcTaskName)
{
    (void)xTask;
    (void)pcTaskName;
    /* Stack overflow detected — halt */
    for (;;);
}

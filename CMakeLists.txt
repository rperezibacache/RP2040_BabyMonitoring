cmake_minimum_required(VERSION 3.13)

# Import Pico SDK and FreeRTOS
include(pico_sdk_import.cmake)
include(FreeRTOS_Kernel_import.cmake)

project(lcd2004_w5500_freertos C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(firmware
    src/main.c
    src/lcd_2004a.c
    src/w5500_driver.c
    src/tsl2561.c
    src/ENS160_HT21.c
)

target_include_directories(firmware PRIVATE src)

target_link_libraries(firmware
    pico_stdlib
    hardware_spi
    hardware_gpio
    hardware_i2c
    FreeRTOS-Kernel
    FreeRTOS-Kernel-Heap4
)

pico_enable_stdio_usb(firmware 1)
pico_enable_stdio_uart(firmware 0)
pico_add_extra_outputs(firmware)
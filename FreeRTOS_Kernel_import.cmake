# FreeRTOS Kernel import for RP2040 SMP port
if (DEFINED ENV{FREERTOS_KERNEL_PATH} AND (NOT FREERTOS_KERNEL_PATH))
    set(FREERTOS_KERNEL_PATH $ENV{FREERTOS_KERNEL_PATH})
    message("Using FREERTOS_KERNEL_PATH from environment ('${FREERTOS_KERNEL_PATH}')")
endif ()

set(FREERTOS_KERNEL_RP2040_RELATIVE_PATH "portable/ThirdParty/GCC/RP2040")

if (NOT FREERTOS_KERNEL_PATH)
    if (EXISTS ${CMAKE_CURRENT_LIST_DIR}/lib/FreeRTOS-Kernel/${FREERTOS_KERNEL_RP2040_RELATIVE_PATH}/port.c)
        set(FREERTOS_KERNEL_PATH ${CMAKE_CURRENT_LIST_DIR}/lib/FreeRTOS-Kernel)
        message("Using FreeRTOS-Kernel from lib/FreeRTOS-Kernel")
    endif ()
endif ()

if (NOT FREERTOS_KERNEL_PATH)
    message(FATAL_ERROR 
        "FreeRTOS-Kernel not found. Set FREERTOS_KERNEL_PATH environment variable "
        "or clone to lib/FreeRTOS-Kernel")
endif ()

get_filename_component(FREERTOS_KERNEL_PATH "${FREERTOS_KERNEL_PATH}" REALPATH BASE_DIR "${CMAKE_BINARY_DIR}")
if (NOT EXISTS ${FREERTOS_KERNEL_PATH})
    message(FATAL_ERROR "Directory '${FREERTOS_KERNEL_PATH}' not found")
endif ()

set(FREERTOS_KERNEL_RP2040_PATH
    ${FREERTOS_KERNEL_PATH}/${FREERTOS_KERNEL_RP2040_RELATIVE_PATH})

if (NOT EXISTS ${FREERTOS_KERNEL_RP2040_PATH}/port.c)
    message(FATAL_ERROR "RP2040 port not found in '${FREERTOS_KERNEL_RP2040_PATH}'")
endif ()

message(STATUS "FreeRTOS-Kernel found at: ${FREERTOS_KERNEL_PATH}")
message(STATUS "RP2040 port path: ${FREERTOS_KERNEL_RP2040_PATH}")

set(FREERTOS_KERNEL_INCLUDE_DIRS
    ${FREERTOS_KERNEL_PATH}/include
    ${FREERTOS_KERNEL_RP2040_PATH}/include
)

add_library(FreeRTOS-Kernel STATIC
    ${FREERTOS_KERNEL_PATH}/tasks.c
    ${FREERTOS_KERNEL_PATH}/list.c
    ${FREERTOS_KERNEL_PATH}/queue.c
    ${FREERTOS_KERNEL_PATH}/timers.c
    ${FREERTOS_KERNEL_PATH}/event_groups.c
    ${FREERTOS_KERNEL_PATH}/stream_buffer.c
    ${FREERTOS_KERNEL_RP2040_PATH}/port.c
)

target_include_directories(FreeRTOS-Kernel PUBLIC
    ${FREERTOS_KERNEL_INCLUDE_DIRS}
    ${CMAKE_CURRENT_LIST_DIR}/src
)

target_link_libraries(FreeRTOS-Kernel PUBLIC
    pico_stdlib
    pico_multicore
    hardware_exception
    hardware_structs
    hardware_irq
)

add_library(FreeRTOS-Kernel-Heap4 INTERFACE)
target_sources(FreeRTOS-Kernel-Heap4 INTERFACE
    ${FREERTOS_KERNEL_PATH}/portable/MemMang/heap_4.c
)
target_link_libraries(FreeRTOS-Kernel-Heap4 INTERFACE FreeRTOS-Kernel)
cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(cpu-rtos C CXX ASM)

pico_sdk_init()

add_executable(cpu-rtos
    mcu-pico.c
)

target_link_libraries(cpu-rtos
    pico_stdlib
)

pico_add_extra_outputs(cpu-rtos)
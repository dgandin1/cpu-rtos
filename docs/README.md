# CPU-RTOS Technical Documentation

Welcome to the comprehensive technical documentation for the **CPU-RTOS** system.

### Master Architecture Document
The complete system specification is consolidated into a single technical reference manual:

* 📖 **[System Architecture & Technical Manual](file:///home/duke/dev/cpu-rtos/docs/system_architecture.md)**
  1. Executive Architecture Overview & Block Diagrams
  2. Master System Memory Map (IRAM, DRAM, VRAM, MMIO, External SRAM)
  3. CPU Core Microarchitecture (5-Stage Pipeline, Forwarding, Hazard Detection)
  4. Instruction Set Architecture (ISA) Specification (14 Instructions)
  5. Memory Subsystem, Dual-Port Hybrid ITCM & L1 Cache
  6. Memory-Mapped I/O Peripherals (VGA 7x Scaler, PIT Timer, MCU Disk FIFO)
  7. Virtual Storage Subsystem & Raspberry Pi Pico RP2040 Firmware
  8. Two-Stage OS Bootloader Architecture & Chained Interrupt Routing
  9. Software Toolchain, C- Compiler, Calling Convention & Pong Game
  10. Hardware Pinout, Physical Wiring & Cocotb Verification Suite

---

### Legacy Notes
* [Architecture.md](file:///home/duke/dev/cpu-rtos/docs/Architecture.md) (Initial unpipelined draft)
* [Software.md](file:///home/duke/dev/cpu-rtos/docs/Software.md) (Initial compiler draft)
* [risc-v-modified.txt](file:///home/duke/dev/cpu-rtos/docs/risc-v-modified.txt) (Instruction encoding scratchpad)

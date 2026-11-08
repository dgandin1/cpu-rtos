# aCPU

A modified RISC-V processor along with a C compiler and RTOS. 

### Documentations

[`Architecture.md`](docs/Architecture.md) - CPU architecture, ISA, and features \
[`Software.md`](docs/Software.md) - Compiler, C- overview, standard library \
[`RTOS.md`]() - WIP \
[`risc-v-modified.txt`](risc-v-modified.txt) - Full instruction encodings

### File Structure

|Path|Purpose|
|----|-------|
|/rtl |Verilog RTL files for CPU|
|/tb  |Testbenches and simulations for CPU|
|/compiler|C- compiler, assembler and related tools|
|/compiler/std|Standard libraries and RTOS for C-|
|/mcu |Code for RP2040 disk emulator|

### Quickstart Simulation

Requirements:
* Python 3.6.2+
* Verilator 5.0+
* Cocotb 2.0+
* Pygame

To compile program, cd into the compiler directory and use the g--.py utility:
```
python g--.py -o program.hex source1.c- 
```
Copy generated binary into `cpu/rtl/sim_build/program.hex`. Run the following command from within the tb directory to launch the graphical simulation:
```
python run_sim.py
```

### Processor features:

* 5-Stage pipelined core @ 100 MHz.
* 512 KB of cached SRAM (32 KB L1 Cache).
* VGA controller and dedicated display buffer.
* 16 KB of single cycle access instruction memory. 
* UART interface for extrenal communication.

### C- features supported:

C- is a subset of C that supports a limited number of features that make it possible to create a wide range of programs. Below are supported C features:
* Variables of types `int`
* `if`, `else`, and `while` statements
* `structs`
* Functions of return type `int` and `void`
* Arrays
* Pointers

More features are planned to be added in the future. See documentation for a more comprehensive overview of current features.

### CPU/RTOS features supported:

* A limited RISC-V like instruction set. See documentation for more details.
* Interrupts (via C- `IRQ_handler()`)
* Task scheduling (software side round robin)
* Integrated PIT
* Builtin VGA MMIO and controller

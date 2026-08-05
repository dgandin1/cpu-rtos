# Architecture

### Overview

The main processing unit is a 32-bit CPU based on a simplified RISC-V architecture. There are 13 total instuctions, designed to keep the processor simple while providing enough flexible to create many programs without too much hassle. The CPU has dedicated IRAM and DRAM as well as interrupt handling capabilities. 

### CPU Layout

Insert image

### Registers

The CPU contains 32 total registers, 29 of which are general purpose. The three registers that have a hardware defined purpose are as follows:

* R0: Hardwired zero
* R26: MCAUSE (interrupt cause register, read only)
* R31: PC (program counter, read only)

While all other registers are technically general purpose, convention is to use the following registers as follows (enforced by compiler):

* R1: Stack pointer
* R3: Function arguments start at R3, and continue to overflow to R4, R5, etc. for subsequent arguments.
* R29: Function return value
* R30: Function return address

### ISA

| Instruction | Semantics | Encoding |
|-------------|-----------|----------|
|`ADD rd r1 r2` |`rd <= r1 + r2`| 
|`SUB rd r1 r2` |`rd <= r1 - r2`|
|`OR rd r1 r2`  |`rd <= r1 OR r2` |
|`AND rd r1 r2` |`rd <= r1 AND r2`|
|`XOR rd r1 r2` |`rd <= r1 XOR r2`|
|`ADDI rd r1 imm`|`rd <= r1 + imm`|
|`LW rd r1 imm`|`rd <= r1[imm]`|
|`SW rs r1 imm`|`r1[imm] <= rs`|
|`BEQ r1 r2 imm`|`if r1 == r2 {PC <= PC + imm}`|
|`BLT r1 r2 imm`|`if r1 < r2 {PC <= PC + imm}`|
|`JMP r1`|`PC <= r1`|
|`MRET`|`PC <= MSPC`|
|`SLL rd r1`|`rd <= r1 << 1`|
|`SRL rd r1`|`rd <= r1 >> 1`|


### Loading programs

Before simulating, the program must be kept in a file named `program.hex` inside the `sim_build` directory. Each line of this file should have one 32 bit instruction in hex form (with no leading `0x`). The program counter will start executing at the first line, and continue sequentially. For JMP instructions, the value in R1 is the line number of the file to jump to (zero based). Reading the PC counter gets the current line number. Branches are relative to the current line number.

### Interrupts

The top-level CPU module takes in a four bit signal titled IRQ_in. Each bit of this signal can be attached to an external device. If the corresponding bit is set high, for the device is set high, and interrupt will trigger and the following will happen:

* PC is saved to internal MSPC register
* MCAUSE is set to the id of the current interrupt (1 for first bit or IRQ_in, 2 for second bit etc.)
* Interrupts are disabled
* PC is set to 0x00000004 (the global interrupt handler address)
* Once an MRET instruction is encountered, the PC is set back to MSPC and interrupts are re-enabled.

Address 0x00000004 in the IRAM must (corresponding to line 5 in `program.hex`) must be set to the IRQ handler code. This is handled internally by the compiler. The IRQ handler must save all registers that it uses, as the hardware does not do this. 

### Memory (DRAM and IO)

The CPU memory consists of DRAM, IRAM and memory mapped IO. IRAM is completely seperate and has its own addressing (see loading programs and interrupts). DRAM and IO share the same address range. The following addresses are configurable but are expected to be mapped to IO by the sims:

0x00000001: stdout
0x00000065-0x0000084D: Display buffer

The rest of memory can be allocated at will.

### Testing and Simulating

The CPU uses Verilator and Cocotb for testing and simulation. A full suite of tests for the CPU can be found in `rtl/tb` and can be run with python. 

To simulate the CPU with the graphical user interface and stdout, ryb `run_sim.py`. This interfaces with the CPU module and uses pygame to display graphics and redirects stdout io to the console.



2:04 PM - Your time zone is 3 h ahead
// cpu_tb_top.v
// Top-level testbench wrapper that connects the CPU core with an off-chip
// SRAM behavioral model for full memory-hierarchy simulation.

`timescale 1ns / 1ps

module cpu_tb_top (
    input  wire       CLK,
    input  wire       RESET,
    input  wire       key_w,
    input  wire       key_s,
    output wire       hsync,
    output wire       vsync,
    output wire [2:0] rgb
);

    // Off-chip physical SRAM interconnect wires
    wire [18:0] MemAdr;
    wire [7:0]  MemDB;
    wire        RamCEn;
    wire        RamOEn;
    wire        RamWEn;

    // CPU core instantiation
    cpu u_cpu (
        .CLK    (CLK),
        .RESET  (RESET),
        .key_w  (key_w),
        .key_s  (key_s),
        .hsync  (hsync),
        .vsync  (vsync),
        .rgb    (rgb),
        .MemAdr (MemAdr),
        .MemDB  (MemDB),
        .RamCEn (RamCEn),
        .RamOEn (RamOEn),
        .RamWEn (RamWEn)
    );

    // Off-chip 512 KB ISSI SRAM behavioral model
    sram_model u_sram (
        .A    (MemAdr),
        .IO   (MemDB),
        .CE_b (RamCEn),
        .OE_b (RamOEn),
        .WE_b (RamWEn)
    );

endmodule

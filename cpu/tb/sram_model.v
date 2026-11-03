// sram_model.v
// Behavioral model of ISSI IS61WV5128BLL (512K x 8-bit Asynchronous SRAM)
// for Verilator & Cocotb verification.

`timescale 1ns / 1ps

module sram_model (
    input  wire [18:0] A,    // 19-bit address (512 KB)
    inout  wire [7:0]  IO,   // 8-bit bidirectional data
    input  wire        CE_b, // Active-low Chip Enable
    input  wire        OE_b, // Active-low Output Enable
    input  wire        WE_b  // Active-low Write Enable
);

    reg [7:0] mem [0:524287];

    // Asynchronous Read: driven when CE=0, OE=0, and WE=1
    wire drive_out = (!CE_b && !OE_b && WE_b);
    assign IO = drive_out ? mem[A] : 8'bzzzz_zzzz;

    // Synchronous write capture on rising edge of WE_b (end of write pulse)
    always @(posedge WE_b) begin
        if (!CE_b) begin
            mem[A] <= IO;
        end
    end

    // Initial memory state: all zeroes
    integer i;
    initial begin
        for (i = 0; i < 524288; i = i + 1) begin
            mem[i] = 8'h00;
        end
    end

endmodule

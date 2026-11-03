module dram (
    input CLK,
    input MW,                  // Memory Write Enable from decoder
    input [31:0] ADDR_A,         // Calculated address from ALU Output
    input [31:0] DATA_IN,      // Data from Register Source B (SB value)
    output reg [31:0] DATA_OUT_A,     // CPU Read Data

    input [31:0] ADDR_B,        // VGA read address
    output reg [31:0] DATA_OUT_B   // VGA Pixel Data
);

    reg [31:0] mem [0:10000];     // 64 words of data memory


    // Synchronous Write (Only happens on clock edge if MW is high)
    always @(posedge CLK) begin
        if (MW) begin
            mem[ADDR_A] <= DATA_IN;
        end
        DATA_OUT_A <= mem[ADDR_A];
    end

    always @(posedge CLK) begin
        DATA_OUT_B <= mem[ADDR_B];
    end

endmodule


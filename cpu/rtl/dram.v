module dram (
    input CLK,
    input MW,                  // Memory Write Enable from decoder
    input [31:0] ADDR,         // Calculated address from ALU Output
    input [31:0] DATA_IN,      // Data from Register Source B (SB value)
    output [31:0] DATA_OUT     // Data sent back to Register File via MD mux
);

    reg [31:0] mem [0:128];     // 64 words of data memory

    // Asynchronous Read
    assign DATA_OUT = mem[ADDR];

    // Synchronous Write (Only happens on clock edge if MW is high)
    always @(posedge CLK) begin
        if (MW) begin
            mem[ADDR] <= DATA_IN;
        end
    end

endmodule

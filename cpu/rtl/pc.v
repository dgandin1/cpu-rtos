module pc(
    input CLK,
    input RESET,
    input [31:0] NEXT_PC,   
    output reg [31:0] PC   
);

    always @(posedge CLK or posedge RESET) begin
        if (RESET)
            PC <= 32'd0;
        else
            PC <= NEXT_PC;
    end

endmodule

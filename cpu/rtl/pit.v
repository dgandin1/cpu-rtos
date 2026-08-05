module pit(CLK, RESET, LD_VALUE, OUT);

    input CLK;
    input RESET;
    input [31:0] LD_VALUE;
    output OUT;

    reg [31:0] current;

    always @(posedge CLK or posedge RESET) begin
        if (RESET)
            current <= 32'd0;
            OUT <= 1'b0;
        if (~RESET && current == LD_VALUE) 
            current <= 32'd0;
            OUT <= 1'b1;
        else
            current = current + 1'b1;
            OUT <= 1'b0;

    end

endmodule
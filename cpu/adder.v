module adder(A, B, CI, Y, C, V);
	
	input [31 : 0] A, B;
	input CI;
	output [31: 0] Y;
	output C, V;

	wire [31:0] COUT;

	genvar i;

    generate
        for (i = 0; i < 32; i = i + 1) begin : FA_CHAIN
            if (i == 0) begin
                fullAdder fa(A[i], B[i], CI, Y[i], COUT[i]);
            end else begin
                fullAdder fa(A[i], B[i], COUT[i-1], Y[i], COUT[i]);
            end
        end
    endgenerate

    assign C = COUT[31];

    // signed overflow detection
    assign V = COUT[31] ^ COUT[30];

endmodule

module fullAdder(A, B, CIN, D, COUT);

	input A, B, CIN;
	output D, COUT;

	assign D = A^B^CIN;
	assign COUT = (A&B) | (A & CIN) | (B&CIN);

endmodule

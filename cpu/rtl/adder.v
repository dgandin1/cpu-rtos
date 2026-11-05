module adder(A, B, CI, Y, C, V);

    input [31 : 0] A, B;
    input CI;
    output [31: 0] Y;
    output C, V;

    // Use a 33-bit intermediate calculation to capture the carry out naturally
    wire [32:0] sum_ext = {1'b0, A} + {1'b0, B} + {{32{1'b0}}, CI};

    assign Y = sum_ext[31:0];
    assign C = sum_ext[32];

    // Signed overflow: true if both inputs have the same sign,
    // but the output sign is different.
    assign V = (A[31] == B[31]) && (Y[31] != A[31]);  // might hae a bug here

endmodule

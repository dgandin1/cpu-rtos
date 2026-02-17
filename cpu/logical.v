module logical(A, B, OA, Y);

    input [31: 0] A, B;
    input OA;

    output [31:0] Y;

    assign Y = (OA ? (A & B) : (A | B));

endmodule
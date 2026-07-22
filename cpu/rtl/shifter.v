//ALU shifter module (supports binary right and left shift)

module shifter(A, LR, Y, C);

    input [31:0] A;
    input LR; // LR = 1 -- shift right, LR = 0 -- shift left
    output [31:0] Y;
    output C;

    wire [31:0] LS;
    wire [31:0] RS;
    wire LSC, RSC;

    genvar i;

    assign LS[0] = 1'b0;
    assign RS[0] = A[1];
    
    for (i = 1; i < 31; i = i + 1) begin
        assign LS[i] = A[i-1];
        assign RS[i] = A[i+1];
    end
    
    assign LS[31] = A[30];
    assign RS[31] = 1'b0;

    assign Y = LR ? RS : LS;
    assign C = LR ? A[0] : A[31];


endmodule

module alu(A, B, FS, Y, C, N, Z, V);

    input [31:0] A;
    input [31:0] B;
    input [2:0]  FS;

    output [31:0] Y;
    output C, V, N, Z;

    wire BSEL;
    wire CISEL;
    wire [1:0] OSEL;
    wire SHIFT_LR;
    wire LOGICAL_OA;
    wire [1:0] CSEL;

    wire [31:0] Y_ADD, Y_LOGICAL, Y_SHIFT;
    wire C_ADD, C_SHIFT;
    wire V_ADD;

    //Modules
    controller c(
        .BSEL(BSEL),
        .CISEL(CISEL),
        .OSEL(OSEL),
        .SHIFT_LR(SHIFT_LR),
        .LOGICAL_OA(LOGICAL_OA),
        .CSEL(CSEL),
        .FS(FS)
    );

    adder add(
        .A(A),
        .B((BSEL ? ~B : B)),
        .CI(CISEL),
        .Y(Y_ADD),
        .C(C_ADD),
        .V(V_ADD)
    );

    logical ld(
        .A(A),
        .B(B),
        .Y(Y_LOGICAL),
        .OA(LOGICAL_OA)
    );

    shifter shift(
        .A(A),
        .Y(Y_SHIFT),
        .C(C_SHIFT),
        .LR(SHIFT_LR)
    );

    //Output Muxes
    assign Y= (OSEL == 2'b00) ? Y_ADD : 
            (OSEL == 2'b01) ? Y_SHIFT :
            (OSEL == 2'b10) ? Y_LOGICAL :
            32'd0;

    //Carry select mux
    assign C = (CSEL == 2'b00) ? C_ADD :
            (CSEL == 2'b01) ? C_SHIFT :
            1'b0;
    
    //Other misc. muxes for flags.
    assign V = (OSEL == 2'b00) ? V_ADD : 1'b0;
    assign N = Y[31] ? 1 : 0;
    assign Z = (Y == 32'd0) ? 1 : 0;


endmodule

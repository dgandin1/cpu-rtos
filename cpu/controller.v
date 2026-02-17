//This is the control logic to set the MUXes in the ALU

module controller(FS, BSEL, CISEL, OSEL, SHIFT_LR, LOGICAL_OA, CSEL);

    input [2: 0] FS;

    localparam FS_ADD = 3'b000;
    localparam FS_SUB = 3'b001;
    localparam FS_SRL = 3'b010;
    localparam FS_SLL = 3'b011;
    localparam FS_AND = 3'b100;
    localparam FS_OR  = 3'b110;

    output reg BSEL; //Invert select
    output reg CISEL;  //Carry in select
    output reg [1:0] OSEL;  //Output module select
    output reg SHIFT_LR;  //Left or right shift
    output reg LOGICAL_OA; //OR or AND
    output reg [1:0] CSEL; //Output carry select


    //Constants:
    always @(*) begin
        case (FS)
            FS_ADD: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b00;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b0;
                CSEL=2'b00;
            end
            FS_SUB: begin
                BSEL = 1'b1;
                CISEL = 1'b1;
                OSEL = 2'b00;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b0;
                CSEL = 2'b00;
            end
            FS_SRL: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b01;
                SHIFT_LR = 1'b1;
                LOGICAL_OA = 1'b0;
                CSEL = 2'b01;
            end 
            FS_SLL: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b01;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b0;
                CSEL = 2'b01;
            end
            FS_AND: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b10;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b1;
                CSEL = 2'b10;
            end
            FS_OR: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b10;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b0;
                CSEL = 2'b10;
            end
            default: begin
                BSEL = 1'b0;
                CISEL = 1'b0;
                OSEL = 2'b00;
                SHIFT_LR = 1'b0;
                LOGICAL_OA = 1'b0;
                CSEL = 2'b00;
            end
        endcase
    end

endmodule
module decoder(INST, DR, SA, SB, IMM, MB, MD, MW, LD, FS);

    input [31:0] INST; 
    output reg[4:0] DR;   //
    output reg [4:0] SA;   // First input register
    output reg [4:0] SB;   // second input register
    output reg [11:0] IMM;  // Ouput register
    output reg MB;         //use SB or IMM
    output reg MW;         // Write to memory
    output reg MD;         // take output from memory or alu
    output reg LD;         // write to output register
    output reg [2:0] FS;   // output opcode

    localparam OP_ARITH     = 7'b0110011;
    localparam OP_IMM_ARITH = 7'b0010011;
    localparam OP_BRANCH    = 7'b1100011;
  //  localparam OP_JAL       = 7'b1101111;
    localparam OP_LW        = 7'b0000011;
    localparam OP_SW        = 7'b0100011;
    localparam OP_JMP       = 7'b0100111;

    // localparam FUN3_ZERO    = 3'b000;
    // localparam FUN3_ONE     = 3'b001;
    // localparam FUN3_TWO     = 3'b010;
    // localparam FUN3_THREE   = 3'b011;
    // localparam FUN3_FOUR    = 3'b100;
    // localparam FUN3_FIVE    = 3'b101;
    // localparam FUN3_SIX     = 3'b110;
    // localparam FUN3_SEVEN   = 3'b111;

    localparam FS_ADD = 3'b000;
    localparam FS_SUB = 3'b001;
    localparam FS_SRL = 3'b010;
    localparam FS_SLL = 3'b011;
    localparam FS_AND = 3'b100;
    localparam FS_OR  = 3'b110;
    localparam FS_XOR = 3'b111;

    localparam IMM_DC       = 12'b000000;
  //  localparam DC_32        = 32'd0;

    always @(*) begin
        
        //defualts
        DR  = 5'b0;
        SA  = 5'b0;
        SB  = 5'b0;
        IMM = 12'b0; // or whatever your IMM width is
        MB  = 1'b0;
        MW  = 1'b0;
        MD  = 1'b0;
        LD  = 1'b0;
        FS  = 3'b0;

        case(INST[6:0])

            OP_ARITH: begin
                DR  = INST[11:7];
                SA  = INST[19:15];
                SB  = INST[24:20];
                IMM = IMM_DC;
                MB  = 1'b0;
                MW  = 1'b0;
                MD  = 1'b0;
                LD  = 1'b1;

                case(INST[14:12])
                    3'b000: begin
                        if (INST[31:25] == 7'b0100000)
                            FS = FS_SUB; // SUBTRACTION
                        else
                            FS = FS_ADD; // ADDITION
                    end
                    3'b001:  FS = FS_SLL; // Shift Left Logical
                    3'b100:  FS = FS_XOR; // XOR (Corrected code point!)
                    3'b101:  FS = FS_SRL; // Shift Right Logical
                    3'b110:  FS = FS_OR;  // OR
                    3'b111:  FS = FS_AND; // AND
                    default: FS = FS_ADD;
                endcase
            end

            

            OP_IMM_ARITH: begin
                
                //ADDI
                DR= INST[11:7];
                SA = INST[19:15];
                SB = 5'b00000;
                IMM = INST[31:20];  //TODO: Fix immediate size!!
                MB = 1'b1;
                MW = 1'b0;
                MD = 1'b0;
                LD = 1'b1;
                FS = FS_ADD;

            end

            OP_LW: begin
                if (INST[14:12] == 3'b010) begin
                    DR = INST[11:7];
                    SA = INST[19:15];
                    SB = 5'b00000;
                    IMM = INST[31:20];
                    MB = 1'b1; // use immediate
                    MW = 1'b0;
                    MD = 1'b1;
                    LD = 1'b1;
                    FS = FS_ADD;
                end
            end

            OP_SW: begin
                DR = 5'b00000;
                SA = INST[19:15];
                SB = INST[11:7];
                IMM = INST[31:20];
                MB = 1'b1;
                MW = 1'b1;
                MD = 1'b0;
                LD = 1'b0;
                FS = FS_ADD;
            end

            OP_BRANCH: begin
                DR = 5'b00000;
                SA = INST[19:15];
                SB = INST[11:7];
                IMM = INST[31:20];
                MB = 1'b0;
                MW = 1'b0;
                MD = 1'b0;
                LD = 1'b0;
                FS = FS_SUB;
            end

            OP_JMP: begin
                DR = 5'b00000;
                SA = INST[19:15];
                SB = 5'd0;
                IMM = IMM_DC;
                MB = 1'b0;
                MW = 1'b0;
                MD = 1'b0;
                LD = 1'b0;
                FS = FS_ADD;
            end

            default: begin
              
            end

            //TODO add branching

        endcase


    end

endmodule

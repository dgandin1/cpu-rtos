module cpu(CLK, RESET, IRQ_in);

    input CLK;
    input RESET;
    input [3:0] IRQ_in; // address of current interrupt (zero if no interrupt)
    wire [31:0] Iin;  // Instruction in

    wire [4:0] SA;
    wire [4:0] SB;
    wire LD;
    wire [4:0] DR;
    wire [11:0] IMM;
    wire [2:0] FS;    
    
    wire MB;
    wire MD;
    wire MW;
    wire [31:0] DataA;
    wire [31:0] DataB;
    
    wire [31:0] PC_next;
    wire [31:0] PC_current; 
    
    wire [31:0] D_in;
    

    wire [31:0] SE_IMM;
    assign SE_IMM = {{20{IMM[11]}}, IMM}; // Extends the 6-bit sign bit to all upper 26 bits

    decoder decode(
        .INST(Iin),
        .DR(DR),
        .SA(SA),
        .SB(SB),
        .IMM(IMM),
        .MB(MB),
        .MD(MD),
        .MW(MW),
        .LD(LD),
        .FS(FS)
    );
    
    regfile register(
        .CLK(CLK),
        .RESET(RESET),
        .SA(SA),
        .SB(SB),
        .LD(LD),
        .DR(DR),
        .D_in(D_in), 
        .DataA(DataA),
        .DataB(DataB)
    );

    wire [31:0] finalDataA;
    assign finalDataA = (SA == 5'd31) ? PC_current : (SA == 5'd26) ? {30'd0, MCAUSE} : DataA;

    pc program_counter(
        .RESET(RESET),
        .CLK(CLK),
        .NEXT_PC(PC_next),
        .PC(PC_current)
    );

    iram instruction_memory (
        .FETCH_ADDR  (PC_current),         // PC points here
        .INSTRUCTION (Iin) // Outputs the raw 32-bit token
    );

    
    wire C;
    wire V;
    wire N;
    wire Z;
    wire [31:0] Alu_Output;
  
    wire [31:0] alu_in_b;
    assign alu_in_b = (MB == 1'b1) ? SE_IMM : DataB;
    
    alu main(
        .A(finalDataA),
        .B(alu_in_b),
        .FS(FS),
        .Y(Alu_Output),
        .C(C),
        .V(V),
        .N(N),
        .Z(Z)
    );

    wire [31:0] dram_data_out;

    dram data_memory (
        .CLK(CLK),
        .MW(MW),
        .ADDR(Alu_Output),
        .DATA_IN(DataB),
        .DATA_OUT(dram_data_out)
    );

    // INTERRUPT LOGIC
    reg MIE; //interrupt enable bit
    reg [31:0] MEPC; // interrupt return address
    wire is_mret; // is a return from interruppt instruction
    assign is_mret = (Iin == 32'h00000073);
    localparam MTVEC = 32'h00000004; // address of ISR
    reg [3:0] irq_pending;
    

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            irq_pending <= 4'b0000;
        end else begin
            // Set pending bits when external inputs go high
            irq_pending <= irq_pending | IRQ_in;
            
            // Clear the bit of the interrupt currently being serviced
            if (~(irq_pending == 4'd0)) begin
                irq_pending[irq_id] <= 1'b0;
            end
        end
    end

    wire [1:0] irq_id;
    assign irq_id = irq_pending[0] ? 2'd0 :
                    irq_pending[1] ? 2'd1 :
                    irq_pending[2] ? 2'd2 : 2'd3;
    
    reg [1:0] MCAUSE;

    always @(posedge CLK or posedge RESET) begin

        if (RESET) begin
            MEPC <= 32'd0;
            MIE <= 1'b1;
            MCAUSE <= 2'd0;
        end else if (~(irq_pending == 4'd0) && MIE) begin
            MEPC <= PC_current;
            MIE <= 1'b0;
            MCAUSE <= irq_id;
        end else if (is_mret) begin
            MIE <= 1'b1;
        end

    end

    assign D_in = (MD) ? dram_data_out : Alu_Output;

    // BRANCHING LOGIC
    wire is_branch;
    wire branch_taken;
    wire [31:0] pc_standard_next;

    assign is_branch = (Iin[6:0] == 7'b1100011 || Iin[6:0] == 7'b0100111);
    assign branch_taken = (Iin[14:12] == 3'b000) ? (is_branch && Z) : (Iin[14:12] == 3'b001) ? (is_branch && N) : is_branch;

    wire [31:0] pc_plus_1;
    wire [31:0] pc_branch_target;

    assign pc_plus_1 = PC_current + 32'd1;
    assign pc_branch_target = (Iin[14:12] == 3'b011) ? Alu_Output : PC_current + SE_IMM;
    assign pc_standard_next = (branch_taken) ? pc_branch_target : pc_plus_1;

    assign PC_next = (~(irq_pending == 4'd0) && MIE) ? MTVEC : (is_mret) ? MEPC : pc_standard_next;


endmodule

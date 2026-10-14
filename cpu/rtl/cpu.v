module cpu(CLK, RESET, key_w, key_s, hsync, vsync, rgb);

    input CLK;
    input RESET;
    wire [3:0] IRQ_in; // address of current interrupt (zero if no interrupt)
    input key_w;
    input key_s;

    assign IRQ_in[1] = key_w;
    assign IRQ_in[2] = key_s;
    assign IRQ_in[0] = 1'b0;
    wire [31:0] Iin;  // Instruction in

    output hsync;
    output vsync;
    output [2:0] rgb;

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
        .INST(if_id_instr),
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
        .LD(mem_wb_ld),
        .DR(mem_wb_dr),
        .D_in(D_in), 
        .DataA(DataA),
        .DataB(DataB)
    );

    wire [31:0] vga_addr;
    wire [31:0] vga_data;

    vga_controller vga(
        .CLK(CLK),
        .RESET(RESET),
        .vram_data(vga_data),
        .vram_addr(vga_addr),
        .rgb(rgb),
        .hsync(hsync),
        .vsync(vsync)
    );

    // Deal with special purpose registers
    wire [31:0] finalDataA;
                            // PC
    assign finalDataA = (SA == 5'd31) ? if_id_pc :
                            // MCAUSE
                        (SA == 5'd26) ? ((mem_wb_ld && (mem_wb_dr == 5'd26)) ? {30'd0, D_in[1:0]} : {30'd0, MCAUSE}) :
                            // MEPC
                        (SA == 5'd27) ? ((mem_wb_ld && (mem_wb_dr == 5'd27)) ? D_in : MEPC) :
                        DataA;

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
  
    // FORWARDING UNIT
    wire [1:0] forward_a;
    assign forward_a = (ex_mem_ld && (ex_mem_dr != 5'd0) && (ex_mem_dr == id_ex_sa)) ? 2'b10 :
                       (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sa)) ? 2'b01 :
                                                                                       2'b00;

    wire [1:0] forward_b;
    assign forward_b = (ex_mem_ld && (ex_mem_dr != 5'd0) && (ex_mem_dr == id_ex_sb)) ? 2'b10 :
                       (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sb)) ? 2'b01 :
                                                                                       2'b00;

    wire [31:0] alu_in_a;
    assign alu_in_a = (forward_a == 2'b10) ? ex_mem_alu_out :
                      (forward_a == 2'b01) ? D_in :
                                             id_ex_data_a;

    wire [31:0] forwarded_data_b;
    assign forwarded_data_b = (forward_b == 2'b10) ? ex_mem_alu_out :
                              (forward_b == 2'b01) ? D_in :
                                                     id_ex_data_b;

    wire [31:0] alu_in_b;
    assign alu_in_b = (id_ex_mb == 1'b1) ? id_ex_se_imm : forwarded_data_b;
    
    alu main(
        .A(alu_in_a),
        .B(alu_in_b),
        .FS(id_ex_fs),
        .Y(Alu_Output),
        .C(C),
        .V(V),
        .N(N),
        .Z(Z)
    );

    wire [31:0] dram_data_out;

    dram data_memory (
        .CLK(CLK),
        .MW(ex_mem_mw),
        .ADDR_A(ex_mem_alu_out),
        .DATA_IN(ex_mem_data_b),
        .DATA_OUT_A(dram_data_out),
        .DATA_OUT_B(vga_data),
        .ADDR_B(vga_addr)
    );

    // INTERRUPT LOGIC
    reg if_id_valid;
    reg MIE; //interrupt enable bit
    reg [31:0] MEPC; // interrupt return address

    localparam MTVEC = 32'h00000004; // address of ISR
    reg [3:0] irq_pending;
    

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            irq_pending <= 4'b0000;
        end else begin
            // Set pending bits when external inputs go high
            irq_pending <= irq_pending | IRQ_in;
            
            // Clear the bit of the interrupt currently being serviced
            if (take_interrupt) begin
                irq_pending[irq_id] <= 1'b0;
            end
        end
    end

    wire [1:0] irq_id;
    assign irq_id = irq_pending[0] ? 2'd0 :
                    irq_pending[1] ? 2'd1 :
                    irq_pending[2] ? 2'd2 : 2'd3;
    
    reg [1:0] MCAUSE;

    wire take_interrupt = (~(irq_pending == 4'd0) && MIE && !load_use_hazard);

    always @(posedge CLK or posedge RESET) begin

        if (RESET) begin
            MEPC <= 32'd0;
            MIE <= 1'b1;
            MCAUSE <= 2'd0;
        end else if (take_interrupt) begin
            MEPC <= (ex_redirect)   ? ex_redirect_target :
                    (!if_id_valid) ? PC_current :
                                     if_id_pc;
            MIE <= 1'b0;
            MCAUSE <= irq_id;
        end else if (id_ex_is_mret) begin
            MIE <= 1'b1;
        end else begin
            if (mem_wb_ld && (mem_wb_dr == 5'd27)) begin
                MEPC <= D_in;
            end 
            if (mem_wb_ld && (mem_wb_dr == 5'd26)) begin
                MCAUSE <= D_in[1:0];
            end 
        end

    end

    // HAZARD DETECTION & BRANCH RESOLUTION
    wire is_load_in_ex = id_ex_md && id_ex_ld && (id_ex_dr != 5'd0);
    wire id_reads_sa   = (SA != 5'd0);
    wire id_reads_sb   = (SB != 5'd0) && (~MB || MW); // reads SB if reg-reg, branch, or store
    wire load_use_hazard = is_load_in_ex && (
        (id_reads_sa && (id_ex_dr == SA)) ||
        (id_reads_sb && (id_ex_dr == SB))
    );

    // Branch Resolution (EX Stage) (see if branch is taken)
    wire ex_branch_taken = (id_ex_func3 == 3'b000) ? (id_ex_is_branch && Z) :
                           (id_ex_func3 == 3'b001) ? (id_ex_is_branch && N) :
                                                     id_ex_is_branch;

    // check if its a JAL
    wire [31:0] ex_branch_target = (id_ex_func3 == 3'b011) ? Alu_Output : id_ex_pc + id_ex_se_imm;
    wire ex_redirect = ex_branch_taken || id_ex_is_mret;
    wire [31:0] ex_redirect_target = (id_ex_is_mret) ? MEPC : ex_branch_target;

    // Pipeline Control
    wire pc_stall    = load_use_hazard && !ex_redirect && !take_interrupt;
    wire if_id_stall = load_use_hazard && !ex_redirect && !take_interrupt;
    wire if_id_flush = ex_redirect || take_interrupt;
    wire id_ex_flush = ex_redirect || load_use_hazard || take_interrupt;

    wire [31:0] pc_plus_1 = PC_current + 32'd1;
    assign PC_next = (take_interrupt) ? MTVEC :
                     (ex_redirect)    ? ex_redirect_target :
                     (pc_stall)       ? PC_current :
                                        pc_plus_1;

    pit timer(
        .CLK(CLK),
        .RESET(RESET),
        .ADDR(ex_mem_alu_out),
        .DATA_IN(ex_mem_data_b),
        .MW(ex_mem_mw),
        .OUT(IRQ_in[3])
    );

    // PIPELINING

    // INSTRUCTION FETCH STAGE

    reg [31:0] if_id_pc;
    reg [31:0] if_id_instr;

    always @(posedge CLK or posedge RESET) begin
        if (RESET || if_id_flush) begin
            if_id_valid <= 1'b0;
            if_id_pc    <= 32'd0;
            if_id_instr <= 32'h00000013; // (addi x0, x0, 0) - NOP
        end else if (!if_id_stall) begin
            if_id_valid <= 1'b1;
            if_id_pc    <= PC_current;
            if_id_instr <= Iin;          
        end
    end

    // INSTRUCTION DECODE STAGE
    wire id_is_branch = if_id_valid && (if_id_instr[6:0] == 7'b1100011 || if_id_instr[6:0] == 7'b0100111);
    wire [2:0] id_func3 = if_id_instr[14:12];
    wire id_is_mret = if_id_valid && (if_id_instr == 32'h00000073);

    reg [31:0] id_ex_pc;
    reg [31:0] id_ex_data_a;
    reg [31:0] id_ex_data_b;
    reg [31:0] id_ex_se_imm;
    reg [4:0]  id_ex_dr;
    reg [4:0]  id_ex_sa;
    reg [4:0]  id_ex_sb;
    reg [2:0]  id_ex_fs;
    reg        id_ex_mb;
    reg        id_ex_mw;
    reg        id_ex_md;
    reg        id_ex_ld;
    reg        id_ex_is_branch;
    reg [2:0]  id_ex_func3;
    reg        id_ex_is_mret;

    always @(posedge CLK or posedge RESET) begin
        if (RESET || id_ex_flush) begin
            id_ex_pc        <= 32'd0;
            id_ex_data_a    <= 32'd0;
            id_ex_data_b    <= 32'd0;
            id_ex_se_imm    <= 32'd0;
            id_ex_dr        <= 5'd0;
            id_ex_sa        <= 5'd0;
            id_ex_sb        <= 5'd0;
            id_ex_fs        <= 3'd0;
            id_ex_mb        <= 1'b0;
            id_ex_mw        <= 1'b0;
            id_ex_md        <= 1'b0;
            id_ex_ld        <= 1'b0;
            id_ex_is_branch <= 1'b0;
            id_ex_func3     <= 3'd0;
            id_ex_is_mret   <= 1'b0;
        end else begin
            id_ex_pc        <= if_id_pc;
            id_ex_data_a    <= finalDataA;
            id_ex_data_b    <= DataB;
            id_ex_se_imm    <= SE_IMM;
            id_ex_dr        <= DR;
            id_ex_sa        <= SA;
            id_ex_sb        <= SB;
            id_ex_fs        <= FS;
            id_ex_mb        <= MB;
            id_ex_mw        <= MW;
            id_ex_md        <= MD;
            id_ex_ld        <= LD;
            id_ex_is_branch <= id_is_branch;
            id_ex_func3     <= id_func3;
            id_ex_is_mret   <= id_is_mret;
        end
    end

    // EXECUTE STAGE

    reg [31:0] ex_mem_alu_out;
    reg [31:0] ex_mem_data_b;     // Store data for DRAM
    reg [4:0]  ex_mem_dr;
    
    // control signs
    reg        ex_mem_mw;
    reg        ex_mem_md;
    reg        ex_mem_ld;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            ex_mem_alu_out <= 32'd0;
            ex_mem_data_b  <= 32'd0;
            ex_mem_dr      <= 5'd0;
            ex_mem_mw      <= 1'b0;
            ex_mem_md      <= 1'b0;
            ex_mem_ld      <= 1'b0;
        end else begin
            ex_mem_alu_out <= Alu_Output;
            ex_mem_data_b  <= forwarded_data_b;
            ex_mem_dr      <= id_ex_dr;
            ex_mem_mw      <= id_ex_mw;
            ex_mem_md      <= id_ex_md;
            ex_mem_ld      <= id_ex_ld;
        end
    end

    // Memeory STAGE

    reg [31:0] mem_wb_alu_out;
    reg [31:0] mem_wb_dram_out;
    reg [4:0]  mem_wb_dr;
    // Control signals
    reg        mem_wb_md;
    reg        mem_wb_ld;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            mem_wb_alu_out  <= 32'd0;
            mem_wb_dram_out <= 32'd0;
            mem_wb_dr       <= 5'd0;
            mem_wb_md       <= 1'b0;
            mem_wb_ld       <= 1'b0;
        end else begin
            mem_wb_alu_out  <= ex_mem_alu_out;
            mem_wb_dram_out <= dram_data_out;
            mem_wb_dr       <= ex_mem_dr;
            mem_wb_md       <= ex_mem_md;
            mem_wb_ld       <= ex_mem_ld;
        end
    end

    // WRITEBACK STAGE

    assign D_in = (mem_wb_md) ? mem_wb_dram_out : mem_wb_alu_out;



`ifdef SYNTHESIS
    ila_0 ila_inst (
    	.clk(CLK),           // Master 100MHz clock
    	.probe0(hsync),      // 1-bit
    	.probe1(vsync),      // 1-bit
    	.probe2(PC_next),    // 32-bit
    	.probe3(rgb),        //3-bit
    	.probe4(IRQ_in)   // 4-bit
    );
`endif


endmodule

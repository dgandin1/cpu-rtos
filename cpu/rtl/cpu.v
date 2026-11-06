module cpu(
    CLK,
    RESET,
    key_w,
    key_s,
    hsync,
    vsync,
    rgb,
    MemAdr,
    MemDB,
    RamCEn,
    RamOEn,
    RamWEn,
    mcu_rx,
    mcu_tx
);

    input CLK;
    input RESET;
    wire [3:0] IRQ_in; // address of current interrupt (zero if no interrupt)
    input key_w;
    input key_s;
    input mcu_rx;
    output mcu_tx;

    assign IRQ_in[1] = key_w;
    assign IRQ_in[2] = key_s;
    assign IRQ_in[0] = 1'b0;
    wire [31:0] Iin;  // Instruction in

    output hsync;
    output vsync;
    output [2:0] rgb;

    // Physical Cmod A7 External SRAM Interface
    output [18:0] MemAdr;
    inout  [7:0]  MemDB;
    output        RamCEn;
    output        RamOEn;
    output        RamWEn;

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

    wire [31:0] iram_data_out;

    iram #(.WORDS(4096)) instruction_memory (
        .CLK         (CLK),
        .FETCH_ADDR  (PC_current),         // PC points here
        .INSTRUCTION (Iin),                // Outputs the raw 32-bit token
        .PORT_B_EN   (is_iram_data && (ex_mem_md || ex_mem_mw)),
        .PORT_B_WE   (ex_mem_mw),
        .PORT_B_ADDR (ex_mem_alu_out - 32'h0008_0000),
        .PORT_B_WDATA(ex_mem_data_b),
        .PORT_B_RDATA(iram_data_out)
    );

    
    wire C;
    wire V;
    wire N;
    wire Z;
    wire [31:0] Alu_Output;
  
    // FORWARDING UNIT
    wire [1:0] forward_a;
    assign forward_a = (ex_mem_ld && (ex_mem_dr != 5'd0) && (ex_mem_dr == id_ex_sa)) ? 2'b10 :
                       (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sa) && !(id_ex_is_branch && mem_wb_md)) ? 2'b01 :
                                                                                       2'b00;

    wire [1:0] forward_b;
    assign forward_b = (ex_mem_ld && (ex_mem_dr != 5'd0) && (ex_mem_dr == id_ex_sb)) ? 2'b10 :
                       (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sb) && !(id_ex_is_branch && mem_wb_md)) ? 2'b01 :
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

    // MEMORY HIERARCHY & ADDRESS DECODING (ALL WORD-ADDRESSED: 1 address = 1 32-bit word)
    // 0..999:                   On-chip BRAM DRAM (including VRAM at 101..228) (1000 words = 4 KB)
    // 1000..0x0001_FFFF:        512 KB External SRAM (via 32 KB L1 Data Cache) (131,072 words = 512 KB)
    // 0x0008_0000..0x0008_0FFF: On-chip BRAM IRAM Port B (4096 words = 16 KB)
    // 0xFFFF_FFB0..0xFFFF_FFB2: Microcontroller Disk MMIO (FIFO Status / Data / Ctrl)
    // 0xFFFF_FFFA:              PIT Timer MMIO
    wire is_pit_mmio           = (ex_mem_alu_out == 32'hFFFF_FFFA);
    wire is_disk_mmio          = (ex_mem_alu_out >= 32'hFFFF_FFB0 && ex_mem_alu_out <= 32'hFFFF_FFB2);
    wire is_mmio               = is_pit_mmio || is_disk_mmio;
    wire is_vram_or_scratchpad = (ex_mem_alu_out < 32'd1000);
    wire is_iram_data          = (ex_mem_alu_out >= 32'h0008_0000 && ex_mem_alu_out < 32'h0008_1000);
    wire is_sram_cache         = !is_mmio && !is_vram_or_scratchpad && !is_iram_data && (ex_mem_md || ex_mem_mw);

    wire [31:0] dram_data_out;
    wire [31:0] cache_data_out;
    wire [31:0] disk_data_out;
    wire        cache_stall;
    wire        cache_ready;

    wire [31:0] mem_stage_data_out = (is_vram_or_scratchpad) ? dram_data_out :
                                     (is_iram_data)          ? iram_data_out :
                                     (is_disk_mmio)          ? disk_data_out :
                                                               cache_data_out;

    dram data_memory (
        .CLK(CLK),
        .MW(ex_mem_mw && is_vram_or_scratchpad),
        .ADDR_A(ex_mem_alu_out),
        .DATA_IN(ex_mem_data_b),
        .DATA_OUT_A(dram_data_out),
        .DATA_OUT_B(vga_data),
        .ADDR_B(vga_addr)
    );

    // SRAM physical controller wires
    wire        sram_req;
    wire        sram_we;
    wire [3:0]  sram_byte_en;
    wire [31:0] sram_addr;
    wire [31:0] sram_wdata;
    wire [31:0] sram_rdata;
    wire        sram_rdy;
    wire        sram_busy;

    cache_controller #(
        .INDEX_BITS(11), // 32 KB L1 Cache
        .LINE_BYTES(16)  // 16 bytes (4 words) per line
    ) l1_dcache (
        .CLK         (CLK),
        .RESET       (RESET),

        // CPU Interface
        .cpu_req     (is_sram_cache),
        .cpu_we      (ex_mem_mw),
        .cpu_byte_en (4'b1111),
        .cpu_addr    (ex_mem_alu_out),
        .cpu_wdata   (ex_mem_data_b),
        .cpu_rdata   (cache_data_out),
        .cpu_stall   (cache_stall),
        .cpu_ready   (cache_ready),

        // Physical SRAM Controller Interface
        .sram_req    (sram_req),
        .sram_we     (sram_we),
        .sram_byte_en(sram_byte_en),
        .sram_addr   (sram_addr),
        .sram_wdata  (sram_wdata),
        .sram_rdata  (sram_rdata),
        .sram_rdy    (sram_rdy),
        .sram_busy   (sram_busy)
    );

    sram sram_ctrl (
        .CLK     (CLK),
        .RESET   (RESET),

        // Cache Interface
        .req     (sram_req),
        .we      (sram_we),
        .byte_en (sram_byte_en),
        .addr_in (sram_addr),
        .data_in (sram_wdata),
        .data_out(sram_rdata),
        .data_rdy(sram_rdy),
        .busy    (sram_busy),

        // External Pins
        .MemAdr  (MemAdr),
        .MemDB   (MemDB),
        .RamCEn  (RamCEn),
        .RamOEn  (RamOEn),
        .RamWEn  (RamWEn)
    );

    // INTERRUPT LOGIC
    reg if_id_valid;
    reg [31:0] if_id_pc;
    reg [31:0] if_id_instr;
    wire id_is_branch = if_id_valid && (if_id_instr[6:0] == 7'b1100011 || if_id_instr[6:0] == 7'b0100111);
    wire [2:0] id_func3 = if_id_instr[14:12];
    wire id_is_mret = if_id_valid && (if_id_instr == 32'h00000073);
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

    wire load_use_hazard;
    wire load_branch_hazard;
    wire take_interrupt = (~(irq_pending == 4'd0) && MIE && !load_use_hazard && !load_branch_hazard && !cache_stall);

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
    assign load_use_hazard = is_load_in_ex && (
        (id_reads_sa && (id_ex_dr == SA)) ||
        (id_reads_sb && (id_ex_dr == SB))
    );

    // Load-to-Branch Hazard: stalls 1 extra cycle if a branch/jump in ID depends on a load in EX/MEM
    wire is_load_in_mem     = ex_mem_md && ex_mem_ld && (ex_mem_dr != 5'd0);
    assign load_branch_hazard = is_load_in_mem && id_is_branch && (
        (id_reads_sa && (ex_mem_dr == SA)) ||
        (id_reads_sb && (ex_mem_dr == SB))
    );

    // Forwarding for Branch / Jump in EX stage:
    // Branches only forward from EX/MEM (ex_mem_alu_out) or from an ALU result in MEM/WB (mem_wb_alu_out).
    // They never forward from a load in MEM/WB because load-to-branch hazards stall 2 cycles,
    // after which the loaded data is already captured in id_ex_data_a / id_ex_data_b.
    // By using mem_wb_alu_out instead of D_in, we decouple the branch comparator from the
    // BRAM/cache read data path, completely eliminating the critical timing path.
    wire [31:0] branch_in_a = (forward_a == 2'b10) ? ex_mem_alu_out :
                              (forward_a == 2'b01) ? mem_wb_alu_out :
                                                     id_ex_data_a;

    wire [31:0] branch_in_b = (forward_b == 2'b10) ? ex_mem_alu_out :
                              (forward_b == 2'b01) ? mem_wb_alu_out :
                                                     id_ex_data_b;

    // Fast Dedicated Branch Comparator (bypasses the 32-bit ALU carry chain and zero reduction tree)
    wire branch_eq = id_ex_is_branch && (branch_in_a == branch_in_b);
    wire branch_lt = id_ex_is_branch && ($signed(branch_in_a) < $signed(branch_in_b));

    // Branch Resolution (EX Stage) (see if branch is taken)
    wire ex_branch_taken = (id_ex_func3 == 3'b000) ? branch_eq :
                           (id_ex_func3 == 3'b001) ? branch_lt :
                                                     id_ex_is_branch;

    // check if its a JAL/JMP (func3 == 3'b011). Bypasses the 32-bit ALU adder since JMP target is directly branch_in_a
    wire [31:0] ex_branch_target = (id_ex_func3 == 3'b011) ? branch_in_a : id_ex_pc + id_ex_se_imm;
    wire ex_redirect = ex_branch_taken || id_ex_is_mret;
    wire [31:0] ex_redirect_target = (id_ex_is_mret) ? MEPC : ex_branch_target;

    // Pipeline Control
    wire pc_stall    = load_use_hazard || load_branch_hazard || cache_stall;
    wire if_id_stall = load_use_hazard || load_branch_hazard || cache_stall;
    wire if_id_flush = (ex_redirect || take_interrupt) && !cache_stall;
    wire id_ex_flush = (ex_redirect || load_use_hazard || load_branch_hazard || take_interrupt) && !cache_stall;

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

    mcu_disk #(
        .CLK_FREQ_HZ(100_000_000),
        .BAUD_RATE  (115_200),
        .FIFO_DEPTH (64)
    ) disk_controller (
        .CLK            (CLK),
        .RESET          (RESET),
        .req            (is_disk_mmio && (ex_mem_md || ex_mem_mw)),
        .we             (ex_mem_mw),
        .addr           (ex_mem_alu_out),
        .wdata          (ex_mem_data_b),
        .rdata          (disk_data_out),
        .mcu_rx         (mcu_rx),
        .mcu_tx         (mcu_tx),
        .sim_inject_en  (1'b0),
        .sim_inject_data(32'd0)
    );

    // PIPELINING

    // INSTRUCTION FETCH STAGE

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            if_id_valid <= 1'b0;
            if_id_pc    <= 32'd0;
            if_id_instr <= 32'h00000013; // (addi x0, x0, 0) - NOP
        end else if (cache_stall) begin
            // Hold fetch register completely during cache stall
        end else if (if_id_flush) begin
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

    // ID/EX Pipeline Registers
    // Control registers: flushed to 0 on RESET or id_ex_flush (converts flushed slot into an inert NOP)
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            id_ex_dr        <= 5'd0;
            id_ex_mw        <= 1'b0;
            id_ex_md        <= 1'b0;
            id_ex_ld        <= 1'b0;
            id_ex_is_branch <= 1'b0;
            id_ex_is_mret   <= 1'b0;
        end else if (cache_stall) begin
            // Hold control registers completely during cache stall
        end else if (id_ex_flush) begin
            id_ex_dr        <= 5'd0;
            id_ex_mw        <= 1'b0;
            id_ex_md        <= 1'b0;
            id_ex_ld        <= 1'b0;
            id_ex_is_branch <= 1'b0;
            id_ex_is_mret   <= 1'b0;
        end else begin
            id_ex_dr        <= DR;
            id_ex_mw        <= MW;
            id_ex_md        <= MD;
            id_ex_ld        <= LD;
            id_ex_is_branch <= id_is_branch;
            id_ex_is_mret   <= id_is_mret;
        end
    end

    // Data payload registers: only cleared on RESET to eliminate high-fanout flush multiplexers
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            id_ex_pc        <= 32'd0;
            id_ex_data_a    <= 32'd0;
            id_ex_data_b    <= 32'd0;
            id_ex_se_imm    <= 32'd0;
            id_ex_sa        <= 5'd0;
            id_ex_sb        <= 5'd0;
            id_ex_fs        <= 3'd0;
            id_ex_mb        <= 1'b0;
            id_ex_func3     <= 3'd0;
        end else if (cache_stall) begin
            if (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sa)) begin
                id_ex_data_a <= D_in;
            end
            if (mem_wb_ld && (mem_wb_dr != 5'd0) && (mem_wb_dr == id_ex_sb)) begin
                id_ex_data_b <= D_in;
            end
        end else begin
            id_ex_pc        <= if_id_pc;
            id_ex_data_a    <= finalDataA;
            id_ex_data_b    <= DataB;
            id_ex_se_imm    <= SE_IMM;
            id_ex_sa        <= SA;
            id_ex_sb        <= SB;
            id_ex_fs        <= FS;
            id_ex_mb        <= MB;
            id_ex_func3     <= id_func3;
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
        end else if (!cache_stall) begin
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
    reg        mem_wb_is_sram;
    reg        mem_wb_is_iram;
    reg        mem_wb_is_disk;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            mem_wb_alu_out  <= 32'd0;
            mem_wb_dram_out <= 32'd0;
            mem_wb_dr       <= 5'd0;
            mem_wb_md       <= 1'b0;
            mem_wb_ld       <= 1'b0;
            mem_wb_is_sram  <= 1'b0;
            mem_wb_is_iram  <= 1'b0;
            mem_wb_is_disk  <= 1'b0;
        end else if (cache_stall) begin
            mem_wb_ld       <= 1'b0;
            mem_wb_md       <= 1'b0;
        end else begin
            mem_wb_alu_out  <= ex_mem_alu_out;
            mem_wb_dram_out <= mem_stage_data_out;
            mem_wb_dr       <= ex_mem_dr;
            mem_wb_md       <= ex_mem_md;
            mem_wb_ld       <= ex_mem_ld;
            mem_wb_is_sram  <= is_sram_cache;
            mem_wb_is_iram  <= is_iram_data;
            mem_wb_is_disk  <= is_disk_mmio;
        end
    end

    // WRITEBACK STAGE

    wire [31:0] wb_mem_data = (mem_wb_is_sram) ? cache_data_out :
                              (mem_wb_is_iram) ? iram_data_out  :
                              (mem_wb_is_disk) ? disk_data_out  :
                                                 dram_data_out;
    assign D_in = (mem_wb_md) ? wb_mem_data : mem_wb_alu_out;



`ifdef SYNTHESIS
    ila_0 ila_inst (
    	.clk(CLK),           // Master 100MHz clock
    	.probe0(hsync),      // 1-bit
    	.probe1(vsync),      // 1-bit
    	.probe2(PC_current), // 32-bit (registered PC output, avoids routing deep combinational PC_next to ILA)
    	.probe3(rgb),        //3-bit
    	.probe4(IRQ_in)   // 4-bit
    );
`endif


endmodule

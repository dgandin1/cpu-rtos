module cache_controller #(
    parameter INDEX_BITS = 11, // 11 = 32 KB (2048 lines), 12 = 64 KB (4096 lines)
    /* verilator lint_off UNUSEDPARAM */
    parameter LINE_BYTES = 16  // 16 bytes = 4 words per cache line
    /* verilator lint_on UNUSEDPARAM */
)(
    // Clock & Reset
    input  wire        CLK,
    input  wire        RESET,

    // CPU Pipeline Interface
    input  wire        cpu_req,        // 1 = CPU is issuing a memory transaction
    input  wire        cpu_we,         // 1 = Write (Store), 0 = Read (Load)
    input  wire [3:0]  cpu_byte_en,    // Byte enable mask (4'b1111 for full word)
    input  wire [31:0] cpu_addr,       // 32-bit address from CPU
    input  wire [31:0] cpu_wdata,      // 32-bit data to store
    output wire [31:0] cpu_rdata,      // 32-bit load data returned to CPU
    output wire        cpu_stall,      // Active-high freeze signal for CPU pipeline
    output reg         cpu_ready,      // 1-cycle active-high completion strobe

    // Physical SRAM Controller Interface (connects to sram.v)
    output reg         sram_req,       // Request pulse to sram.v
    output reg         sram_we,        // 0 = Read, 1 = Write to sram.v
    output reg  [3:0]  sram_byte_en,   // Byte enable to sram.v
    output reg  [31:0] sram_addr,      // Byte address to sram.v
    output reg  [31:0] sram_wdata,     // Write data to sram.v
    input  wire [31:0] sram_rdata,     // Read data from sram.v
    input  wire        sram_rdy,       // Completion pulse from sram.v
    input  wire        sram_busy       // High while sram.v is executing
);

    // -------------------------------------------------------------------------
    // Cache Geometry Calculations (Word-Addressed Architecture)
    // -------------------------------------------------------------------------
    localparam NUM_LINES    = (1 << INDEX_BITS);              // 2048 lines for 32 KB (8192 words)
    localparam OFFSET_WORDS = 2;                              // 4 words (16 bytes) per cache line (2 bits)
    localparam TAG_BITS     = 32 - INDEX_BITS - OFFSET_WORDS; // 19 bits for 32 KB
    localparam EPOCH_BITS   = 8;                              // 8-bit flash invalidation epoch
    localparam ENTRY_BITS   = TAG_BITS + EPOCH_BITS;          // 27 bits total per tag entry

    // -------------------------------------------------------------------------
    // BRAM Storage for Cache Data (4 Banks of 32-bit words = 16 bytes per line)
    // -------------------------------------------------------------------------
    (* ram_style = "block" *) reg [31:0] bank0 [0:NUM_LINES-1];
    (* ram_style = "block" *) reg [31:0] bank1 [0:NUM_LINES-1];
    (* ram_style = "block" *) reg [31:0] bank2 [0:NUM_LINES-1];
    (* ram_style = "block" *) reg [31:0] bank3 [0:NUM_LINES-1];

    // -------------------------------------------------------------------------
    // Distributed RAM for Tags + Epoch
    // Single-cycle flash invalidation on RESET via epoch counter!
    // Asynchronous read enables 0-cycle combinational hit detection in MEM stage.
    // Eliminates 2048-bit valid FF vector and its massive multiplexer tree.
    // -------------------------------------------------------------------------
    (* ram_style = "distributed" *) reg [ENTRY_BITS-1:0] tag_mem [0:NUM_LINES-1];

    reg [EPOCH_BITS-1:0] cache_epoch;
    reg reset_d;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            reset_d <= 1'b1;
        end else begin
            if (reset_d) begin
                cache_epoch <= cache_epoch + 8'd1;
                reset_d     <= 1'b0;
            end
        end
    end

    // Address Decoding (Strictly Word-Addressed: 1 address = 1 32-bit word)
    wire [INDEX_BITS-1:0] cpu_index = cpu_addr[OFFSET_WORDS +: INDEX_BITS];
    wire [TAG_BITS-1:0]   cpu_tag   = cpu_addr[31 -: TAG_BITS];
    wire [1:0]            cpu_word  = cpu_addr[1:0];

    wire [ENTRY_BITS-1:0] tag_dout  = tag_mem[cpu_index];
    wire                  tag_match = (tag_dout == {cache_epoch, cpu_tag});

    wire                  read_hit   = cpu_req && !cpu_we && tag_match;
    wire                  read_miss  = cpu_req && !cpu_we && !tag_match;
    wire                  write_req  = cpu_req && cpu_we;

    // -------------------------------------------------------------------------
    // FSM States
    // -------------------------------------------------------------------------
    localparam S_IDLE        = 3'd0;
    localparam S_REFILL_REQ  = 3'd1;
    localparam S_REFILL_WAIT = 3'd2;
    localparam S_WRITE_REQ   = 3'd3;
    localparam S_WRITE_WAIT  = 3'd4;
    localparam S_DONE        = 3'd5;

    reg [2:0]  state;

    // Miss / Refill Tracking Registers
    reg [INDEX_BITS-1:0] miss_index;
    reg [TAG_BITS-1:0]   miss_tag;
    reg [1:0]            miss_word;
    reg [1:0]            refill_word_idx;
    reg [31:0]           refill_target_data;
    reg                  is_refill_data;

    // BRAM Write Port Signals
    reg [INDEX_BITS-1:0] wr_addr;
    reg [31:0]           wr_data;
    reg                  wr_bank0;
    reg                  wr_bank1;
    reg                  wr_bank2;
    reg                  wr_bank3;
    reg                  wr_tag;
    reg [ENTRY_BITS-1:0] wr_tag_data;

    // Synchronous BRAM Writes
    always @(posedge CLK) begin
        if (wr_bank0) bank0[wr_addr] <= wr_data;
        if (wr_bank1) bank1[wr_addr] <= wr_data;
        if (wr_bank2) bank2[wr_addr] <= wr_data;
        if (wr_bank3) bank3[wr_addr] <= wr_data;
        if (wr_tag)   tag_mem[wr_addr] <= wr_tag_data;
    end

    // Synchronous BRAM Reads (Port B): Addressed directly by cpu_index
    reg [31:0] bank0_dout;
    reg [31:0] bank1_dout;
    reg [31:0] bank2_dout;
    reg [31:0] bank3_dout;
    reg [1:0]  wb_word;

    always @(posedge CLK) begin
        bank0_dout <= bank0[cpu_index];
        bank1_dout <= bank1[cpu_index];
        bank2_dout <= bank2[cpu_index];
        bank3_dout <= bank3[cpu_index];
        if (!cpu_stall) begin
            wb_word <= cpu_word;
        end else if (state == S_DONE) begin
            wb_word <= miss_word;
        end
    end

    // Combinational Word Selection for Read Hit
    wire [31:0] bram_hit_data = (wb_word == 2'd0) ? bank0_dout :
                                (wb_word == 2'd1) ? bank1_dout :
                                (wb_word == 2'd2) ? bank2_dout :
                                                    bank3_dout;

    // Output Data: Select between refilled word or BRAM hit word
    assign cpu_rdata = (is_refill_data) ? refill_target_data : bram_hit_data;

    // Pipeline Freeze Signal:
    // S_IDLE: 0 if Read Hit or Idle; 1 if Read Miss or Write
    // S_DONE: 0 (release freeze for 1 cycle to allow instruction to retire)
    // S_REFILL_*, S_WRITE_*: 1 (keep pipeline frozen)
    assign cpu_stall = (state == S_IDLE) ? (read_miss || write_req) :
                       (state == S_DONE) ? 1'b0 :
                                           1'b1;

    // -------------------------------------------------------------------------
    // Main Cache Controller FSM
    // -------------------------------------------------------------------------
    integer i;
    initial begin
        cache_epoch = 8'd1;
        reset_d     = 1'b0;
        for (i = 0; i < NUM_LINES; i = i + 1) begin
            tag_mem[i] = {ENTRY_BITS{1'b0}};
        end
    end

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            state              <= S_IDLE;
            cpu_ready          <= 1'b0;
            sram_req           <= 1'b0;
            sram_we            <= 1'b0;
            sram_byte_en       <= 4'b1111;
            sram_addr          <= 32'd0;
            sram_wdata         <= 32'd0;
            wr_addr            <= {INDEX_BITS{1'b0}};
            wr_data            <= 32'd0;
            wr_bank0           <= 1'b0;
            wr_bank1           <= 1'b0;
            wr_bank2           <= 1'b0;
            wr_bank3           <= 1'b0;
            wr_tag             <= 1'b0;
            wr_tag_data        <= {ENTRY_BITS{1'b0}};
            miss_index         <= {INDEX_BITS{1'b0}};
            miss_tag           <= {TAG_BITS{1'b0}};
            miss_word          <= 2'd0;
            refill_word_idx    <= 2'd0;
            refill_target_data <= 32'd0;
            is_refill_data     <= 1'b0;
        end else begin
            // Default single-cycle strobes
            cpu_ready      <= 1'b0;
            sram_req       <= 1'b0;
            wr_bank0       <= 1'b0;
            wr_bank1       <= 1'b0;
            wr_bank2       <= 1'b0;
            wr_bank3       <= 1'b0;
            wr_tag         <= 1'b0;
            is_refill_data <= 1'b0;

            case (state)
                // -------------------------------------------------------------
                // S_IDLE: Handle 1-Cycle Read Hits or initiate Miss / Store
                // -------------------------------------------------------------
                S_IDLE: begin
                    if (cpu_req) begin
                        if (cpu_we) begin
                            // Store: initiate write-through to physical SRAM
                            miss_index <= cpu_index;
                            miss_tag   <= cpu_tag;
                            miss_word  <= cpu_word;
                            state      <= S_WRITE_REQ;
                        end else if (!tag_match) begin
                            // Read Miss: freeze pipeline and initiate 16-byte refill
                            miss_index      <= cpu_index;
                            miss_tag        <= cpu_tag;
                            miss_word       <= cpu_word;
                            refill_word_idx <= 2'd0;
                            state           <= S_REFILL_REQ;
                        end else begin
                            // Read Hit: 0 stall cycles! Completes synchronously.
                            cpu_ready <= 1'b1;
                        end
                    end
                end

                // -------------------------------------------------------------
                // S_REFILL_REQ: Request next word from sram.v
                // -------------------------------------------------------------
                S_REFILL_REQ: begin
                    if (!sram_busy) begin
                        sram_req     <= 1'b1;
                        sram_we      <= 1'b0;
                        sram_byte_en <= 4'b1111;
                        sram_addr    <= {miss_tag, miss_index, refill_word_idx};
                        state        <= S_REFILL_WAIT;
                    end
                end

                // -------------------------------------------------------------
                // S_REFILL_WAIT: Latch word from sram.v into target BRAM bank
                // -------------------------------------------------------------
                S_REFILL_WAIT: begin
                    if (sram_rdy) begin
                        wr_addr  <= miss_index;
                        wr_data  <= sram_rdata;
                        wr_bank0 <= (refill_word_idx == 2'd0);
                        wr_bank1 <= (refill_word_idx == 2'd1);
                        wr_bank2 <= (refill_word_idx == 2'd2);
                        wr_bank3 <= (refill_word_idx == 2'd3);

                        // Capture the word requested by CPU
                        if (refill_word_idx == miss_word) begin
                            refill_target_data <= sram_rdata;
                        end

                        if (refill_word_idx == 2'd3) begin
                            // All 4 words filled: update tag and set epoch
                            wr_tag      <= 1'b1;
                            wr_tag_data <= {cache_epoch, miss_tag};
                            state       <= S_DONE;
                        end else begin
                            refill_word_idx <= refill_word_idx + 2'd1;
                            state           <= S_REFILL_REQ;
                        end
                    end
                end

                // -------------------------------------------------------------
                // S_WRITE_REQ: Launch write transaction to physical SRAM
                // -------------------------------------------------------------
                S_WRITE_REQ: begin
                    if (!sram_busy) begin
                        sram_req     <= 1'b1;
                        sram_we      <= 1'b1;
                        sram_byte_en <= (cpu_byte_en == 4'b0000) ? 4'b1111 : cpu_byte_en;
                        sram_addr    <= cpu_addr;
                        sram_wdata   <= cpu_wdata;

                        // If line is valid in cache, update BRAM
                        if (tag_match) begin
                            wr_addr  <= cpu_index;
                            wr_data  <= cpu_wdata;
                            wr_bank0 <= (cpu_word == 2'd0);
                            wr_bank1 <= (cpu_word == 2'd1);
                            wr_bank2 <= (cpu_word == 2'd2);
                            wr_bank3 <= (cpu_word == 2'd3);
                        end

                        state <= S_WRITE_WAIT;
                    end
                end

                // -------------------------------------------------------------
                // S_WRITE_WAIT: Wait for physical SRAM write to complete
                // -------------------------------------------------------------
                S_WRITE_WAIT: begin
                    if (sram_rdy) begin
                        state <= S_DONE;
                    end
                end

                // -------------------------------------------------------------
                // S_DONE: Deassert cpu_stall for 1 cycle to let instruction retire
                // -------------------------------------------------------------
                S_DONE: begin
                    cpu_ready      <= 1'b1;
                    is_refill_data <= 1'b1; // Forward refilled word to WB stage
                    state          <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule

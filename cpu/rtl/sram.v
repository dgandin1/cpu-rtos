module sram (
    // Clock & Reset
    input  wire        CLK,
    input  wire        RESET,

    // CPU / Cache Subsystem Interface
    input  wire        req,            // 1-cycle transaction request
    input  wire        we,             // 0 = Read, 1 = Write
    input  wire [3:0]  byte_en,        // Byte enables (4'b1111 for full 32-bit word)
    input  wire [31:0] addr_in,        // 32-bit address
    input  wire [31:0] data_in,        // 32-bit write data
    output reg  [31:0] data_out,       // 32-bit read data
    output reg         data_rdy,       // 1-cycle active-high completion strobe
    output wire        busy,           // High while transaction is in flight

    // Physical Cmod A7 ISSI IS61WV5128BLL SRAM Pins
    output reg  [18:0] MemAdr,         // 19-bit physical byte address (512 KB)
    inout  wire [7:0]  MemDB,          // Bidirectional 8-bit data bus
    output reg         RamCEn,         // Active-low Chip Enable
    output reg         RamOEn,         // Active-low Output Enable
    output reg         RamWEn          // Active-low Write Enable
);

    // -------------------------------------------------------------
    // FSM States
    // -------------------------------------------------------------
    localparam STATE_IDLE   = 2'd0;
    localparam STATE_ACCESS = 2'd1;
    localparam STATE_DONE   = 2'd2;

    reg [1:0] state;
    reg [1:0] byte_idx;    // Current byte: 0, 1, 2, 3
    reg       cycle_phase; // 0 = Setup/Drive address & control, 1 = Hold/Sample data

    // Latched transaction parameters
    reg [18:0] base_addr;
    reg [31:0] wdata;
    reg [3:0]  latched_be;
    reg        is_we;

    // Default byte mask to 4'b1111 if 0 is passed
    wire [3:0] actual_be = (byte_en == 4'b0000) ? 4'b1111 : byte_en;

    // Tri-state buffer for bidirectional MemDB bus
    reg [7:0] db_out;
    reg       db_oe;
    assign MemDB = db_oe ? db_out : 8'bzzzz_zzzz;

    assign busy = (state != STATE_IDLE);

    // -------------------------------------------------------------
    // FSM Controller Logic (2 Clock Cycles @ 100 MHz per Byte = 20 ns)
    // -------------------------------------------------------------
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            state       <= STATE_IDLE;
            data_rdy    <= 1'b0;
            data_out    <= 32'd0;
            byte_idx    <= 2'd0;
            cycle_phase <= 1'b0;
            base_addr   <= 19'd0;
            wdata       <= 32'd0;
            latched_be  <= 4'b1111;
            is_we       <= 1'b0;
            MemAdr      <= 19'd0;
            RamCEn      <= 1'b1; // Inactive (active-low)
            RamOEn      <= 1'b1; // Inactive (active-low)
            RamWEn      <= 1'b1; // Inactive (active-low)
            db_oe       <= 1'b0;
            db_out      <= 8'd0;
        end else begin
            data_rdy <= 1'b0;

            case (state)
                // -------------------------------------------------
                // STATE_IDLE: Wait for transaction request
                // -------------------------------------------------
                STATE_IDLE: begin
                    RamCEn      <= 1'b1;
                    RamOEn      <= 1'b1;
                    RamWEn      <= 1'b1;
                    db_oe       <= 1'b0;
                    byte_idx    <= 2'd0;
                    cycle_phase <= 1'b0;

                    if (req) begin
                        base_addr   <= addr_in[18:0] & ~19'd3; // 4-byte align
                        wdata       <= data_in;
                        latched_be  <= actual_be;
                        is_we       <= we;
                        state       <= STATE_ACCESS;

                        // Start Byte 0 setup immediately
                        MemAdr <= addr_in[18:0] & ~19'd3;
                        RamCEn <= 1'b0; // Select SRAM chip
                        if (we) begin
                            RamOEn <= 1'b1;
                            RamWEn <= ~actual_be[0]; // Active-low write strobe if enabled
                            db_oe  <= 1'b1;
                            db_out <= data_in[7:0];
                        end else begin
                            RamOEn <= 1'b0;          // Output enable for SRAM read
                            RamWEn <= 1'b1;
                            db_oe  <= 1'b0;          // FPGA pins in high-Z
                        end
                    end
                end

                // -------------------------------------------------
                // STATE_ACCESS: Sequences 4 bytes (2 cycles each = 20 ns)
                // -------------------------------------------------
                STATE_ACCESS: begin
                    if (cycle_phase == 1'b0) begin
                        // Phase 0 -> Phase 1: Hold address/data for SRAM t_AA access time
                        cycle_phase <= 1'b1;
                        if (is_we) begin
                            RamWEn <= 1'b1; // Deassert write enable (write strobe completes)
                        end
                    end else begin
                        // Phase 1: Sample data (Read) or advance to next byte (Write)
                        cycle_phase <= 1'b0;

                        if (!is_we) begin
                            case (byte_idx)
                                2'd0: data_out[7:0]   <= MemDB;
                                2'd1: data_out[15:8]  <= MemDB;
                                2'd2: data_out[23:16] <= MemDB;
                                2'd3: data_out[31:24] <= MemDB;
                            endcase
                        end

                        if (byte_idx == 2'd3) begin
                            // All 4 bytes complete -> Go to DONE
                            RamCEn   <= 1'b1;
                            RamOEn   <= 1'b1;
                            RamWEn   <= 1'b1;
                            db_oe    <= 1'b0;
                            data_rdy <= 1'b1; // Pulse ready
                            state    <= STATE_DONE;
                        end else begin
                            // Advance to next byte
                            byte_idx <= byte_idx + 2'd1;
                            MemAdr   <= base_addr + {17'd0, byte_idx + 2'd1};
                            if (is_we) begin
                                case (byte_idx + 2'd1)
                                    2'd1: begin
                                        db_out <= wdata[15:8];
                                        RamWEn <= ~latched_be[1];
                                    end
                                    2'd2: begin
                                        db_out <= wdata[23:16];
                                        RamWEn <= ~latched_be[2];
                                    end
                                    2'd3: begin
                                        db_out <= wdata[31:24];
                                        RamWEn <= ~latched_be[3];
                                    end
                                    default: begin
                                        db_out <= 8'd0;
                                        RamWEn <= 1'b1;
                                    end
                                endcase
                            end
                        end
                    end
                end

                // -------------------------------------------------
                // STATE_DONE: Deassert ready and return to IDLE cleanly
                // -------------------------------------------------
                STATE_DONE: begin
                    data_rdy <= 1'b0;
                    state    <= STATE_IDLE;
                end

                default: state <= STATE_IDLE;
            endcase
        end
    end

endmodule

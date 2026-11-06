// mcu_disk.v
// Memory-mapped Microcontroller "Disk" Interface
// Connects an external microcontroller (ESP32, RP2040, Arduino, etc.) to the CPU.
//
// Register Map (Base: 0xFFFF_FFB0):
//   0xFFFF_FFB0: DISK_STATUS (Read-Only)
//     - Bit 0:    RX_READY (1 if at least one 32-bit word is available in FIFO)
//     - Bit 1:    RX_FULL  (1 if RX FIFO is completely full)
//     - Bit 2:    TX_BUSY  (1 if UART transmitter is sending a byte)
//     - Bits 15:8 Words available in RX FIFO (0 to 64)
//
//   0xFFFF_FFB1: DISK_DATA (Read / Write)
//     - READ:  Pops and returns the next 32-bit instruction/data word from FIFO
//     - WRITE: Transmits wdata[7:0] to the external microcontroller via mcu_tx
//
//   0xFFFF_FFB2: DISK_CTRL (Write-Only)
//     - WRITE 1: Flushes and resets the RX FIFO

module mcu_disk #(
    parameter CLK_FREQ_HZ = 100_000_000,
    parameter BAUD_RATE   = 115_200,
    parameter FIFO_DEPTH  = 64
)(
    input  wire        CLK,
    input  wire        RESET,

    // Bus Interface from CPU EX/MEM Stage
    input  wire        req,       // Active when address matches DISK MMIO
    input  wire        we,        // 1 = Write, 0 = Read
    input  wire [31:0] addr,      // 0xFFFF_FFB0, 0xFFFF_FFB1, 0xFFFF_FFB2
    input  wire [31:0] wdata,     // Write data from CPU (ex_mem_data_b)
    output reg  [31:0] rdata,     // Read data to CPU writeback stage

    // Physical Pins to External Microcontroller
    input  wire        mcu_rx,    // UART RX from Microcontroller TX
    output reg         mcu_tx,    // UART TX to Microcontroller RX

    // Direct Injection Port for Fast Simulation / Testing
    input  wire        sim_inject_en,
    input  wire [31:0] sim_inject_data
);

    localparam [15:0] CLKS_PER_BIT = CLK_FREQ_HZ / BAUD_RATE; // 868 cycles @ 100MHz / 115200 baud
    localparam [5:0]  FIFO_MAX_PTR = FIFO_DEPTH - 1;

    // -------------------------------------------------------------
    // 1. 2-Stage Synchronizer for Asynchronous mcu_rx Pin
    // -------------------------------------------------------------
    reg [1:0] rx_sync;
    always @(posedge CLK or posedge RESET) begin
        if (RESET)
            rx_sync <= 2'b11;
        else
            rx_sync <= {rx_sync[0], mcu_rx};
    end
    wire rx_in = rx_sync[1];

    // -------------------------------------------------------------
    // 2. Hardware UART Receiver (8-N-1)
    // -------------------------------------------------------------
    localparam RX_IDLE  = 2'd0;
    localparam RX_START = 2'd1;
    localparam RX_DATA  = 2'd2;
    localparam RX_STOP  = 2'd3;

    reg [1:0]  rx_state;
    reg [15:0] rx_clk_cnt;
    reg [2:0]  rx_bit_idx;
    reg [7:0]  rx_shift_reg;
    reg [7:0]  rx_byte_out;
    reg        rx_byte_valid;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            rx_state      <= RX_IDLE;
            rx_clk_cnt    <= 16'd0;
            rx_bit_idx    <= 3'd0;
            rx_shift_reg  <= 8'd0;
            rx_byte_out   <= 8'd0;
            rx_byte_valid <= 1'b0;
        end else begin
            rx_byte_valid <= 1'b0;

            case (rx_state)
                RX_IDLE: begin
                    rx_clk_cnt <= 16'd0;
                    rx_bit_idx <= 3'd0;
                    if (rx_in == 1'b0) begin // Start bit detected
                        rx_state <= RX_START;
                    end
                end

                RX_START: begin
                    // Sample at the middle of the start bit
                    if (rx_clk_cnt == (CLKS_PER_BIT / 2)) begin
                        if (rx_in == 1'b0) begin
                            rx_clk_cnt <= 16'd0;
                            rx_state   <= RX_DATA;
                        end else begin
                            rx_state   <= RX_IDLE; // Glitch filter
                        end
                    end else begin
                        rx_clk_cnt <= rx_clk_cnt + 16'd1;
                    end
                end

                RX_DATA: begin
                    if (rx_clk_cnt == (CLKS_PER_BIT - 1)) begin
                        rx_clk_cnt               <= 16'd0;
                        rx_shift_reg[rx_bit_idx] <= rx_in;
                        if (rx_bit_idx == 3'd7) begin
                            rx_state <= RX_STOP;
                        end else begin
                            rx_bit_idx <= rx_bit_idx + 3'd1;
                        end
                    end else begin
                        rx_clk_cnt <= rx_clk_cnt + 16'd1;
                    end
                end

                RX_STOP: begin
                    // Wait for stop bit duration
                    if (rx_clk_cnt == (CLKS_PER_BIT - 1)) begin
                        rx_state      <= RX_IDLE;
                        rx_byte_out   <= rx_shift_reg;
                        rx_byte_valid <= 1'b1;
                    end else begin
                        rx_clk_cnt <= rx_clk_cnt + 16'd1;
                    end
                end

                default: rx_state <= RX_IDLE;
            endcase
        end
    end

    // -------------------------------------------------------------
    // 3. Byte-to-Word Assembler (Little-Endian: 4 bytes -> 1 32-bit Word)
    // -------------------------------------------------------------
    reg [1:0]  byte_cnt;
    reg [31:0] assembled_word;
    reg        word_ready_to_push;
    reg [31:0] word_to_push;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            byte_cnt           <= 2'd0;
            assembled_word     <= 32'd0;
            word_ready_to_push <= 1'b0;
            word_to_push       <= 32'd0;
        end else begin
            word_ready_to_push <= 1'b0;

            if (rx_byte_valid) begin
                case (byte_cnt)
                    2'd0: assembled_word[7:0]   <= rx_byte_out;
                    2'd1: assembled_word[15:8]  <= rx_byte_out;
                    2'd2: assembled_word[23:16] <= rx_byte_out;
                    2'd3: begin
                        word_to_push       <= {rx_byte_out, assembled_word[23:0]};
                        word_ready_to_push <= 1'b1;
                    end
                endcase
                byte_cnt <= byte_cnt + 2'd1;
            end
        end
    end

    // -------------------------------------------------------------
    // 4. Word FIFO Buffer (Stores incoming 32-bit program words)
    // -------------------------------------------------------------
    (* ram_style = "distributed" *) reg [31:0] fifo_mem [0:FIFO_DEPTH-1];
    reg [5:0]  wr_ptr;
    reg [5:0]  rd_ptr;
    reg [6:0]  fifo_count;

    wire fifo_push = (word_ready_to_push || sim_inject_en) && (fifo_count < FIFO_DEPTH);
    wire [31:0] fifo_push_data = sim_inject_en ? sim_inject_data : word_to_push;
    
    // Read from FIFO happens when CPU reads 0xFFFF_FFB1
    wire fifo_pop = req && !we && (addr == 32'hFFFF_FFB1) && (fifo_count > 0);

    // Dedicated RAM write logic (completely independent of CPU flush/req path)
    always @(posedge CLK) begin
        if (fifo_push) begin
            fifo_mem[wr_ptr] <= fifo_push_data;
        end
    end

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            wr_ptr     <= 6'd0;
            rd_ptr     <= 6'd0;
            fifo_count <= 7'd0;
        end else if (req && we && (addr == 32'hFFFF_FFB2) && wdata[0]) begin
            // DISK_CTRL write 1: Flush FIFO
            wr_ptr     <= 6'd0;
            rd_ptr     <= 6'd0;
            fifo_count <= 7'd0;
        end else begin
            if (fifo_push) begin
                wr_ptr <= (wr_ptr == FIFO_MAX_PTR) ? 6'd0 : wr_ptr + 6'd1;
            end

            if (fifo_pop) begin
                rd_ptr <= (rd_ptr == FIFO_MAX_PTR) ? 6'd0 : rd_ptr + 6'd1;
            end

            case ({fifo_push, fifo_pop})
                2'b10: fifo_count <= fifo_count + 7'd1;
                2'b01: fifo_count <= fifo_count - 7'd1;
                default: fifo_count <= fifo_count; // Both or neither
            endcase
        end
    end

    // -------------------------------------------------------------
    // 5. Hardware UART Transmitter (CPU -> Microcontroller)
    // -------------------------------------------------------------
    localparam TX_IDLE  = 2'd0;
    localparam TX_START = 2'd1;
    localparam TX_DATA  = 2'd2;
    localparam TX_STOP  = 2'd3;

    reg [1:0]  tx_state;
    reg [15:0] tx_clk_cnt;
    reg [2:0]  tx_bit_idx;
    reg [7:0]  tx_shift_reg;
    reg        tx_busy;

    wire tx_start_req = req && we && (addr == 32'hFFFF_FFB1) && !tx_busy;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            tx_state     <= TX_IDLE;
            tx_clk_cnt   <= 16'd0;
            tx_bit_idx   <= 3'd0;
            tx_shift_reg <= 8'd0;
            mcu_tx       <= 1'b1; // UART idle high
            tx_busy      <= 1'b0;
        end else begin
            case (tx_state)
                TX_IDLE: begin
                    mcu_tx     <= 1'b1;
                    tx_clk_cnt <= 16'd0;
                    tx_bit_idx <= 3'd0;
                    if (tx_start_req) begin
                        tx_shift_reg <= wdata[7:0];
                        mcu_tx       <= 1'b0; // Start bit
                        tx_busy      <= 1'b1;
                        tx_state     <= TX_START;
                    end else begin
                        tx_busy      <= 1'b0;
                    end
                end

                TX_START: begin
                    if (tx_clk_cnt == (CLKS_PER_BIT - 1)) begin
                        tx_clk_cnt <= 16'd0;
                        mcu_tx     <= tx_shift_reg[0];
                        tx_state   <= TX_DATA;
                    end else begin
                        tx_clk_cnt <= tx_clk_cnt + 16'd1;
                    end
                end

                TX_DATA: begin
                    if (tx_clk_cnt == (CLKS_PER_BIT - 1)) begin
                        tx_clk_cnt <= 16'd0;
                        if (tx_bit_idx == 3'd7) begin
                            mcu_tx   <= 1'b1; // Stop bit
                            tx_state <= TX_STOP;
                        end else begin
                            tx_bit_idx <= tx_bit_idx + 3'd1;
                            mcu_tx     <= tx_shift_reg[tx_bit_idx + 3'd1];
                        end
                    end else begin
                        tx_clk_cnt <= tx_clk_cnt + 16'd1;
                    end
                end

                TX_STOP: begin
                    if (tx_clk_cnt == (CLKS_PER_BIT - 1)) begin
                        tx_state <= TX_IDLE;
                        tx_busy  <= 1'b0;
                    end else begin
                        tx_clk_cnt <= tx_clk_cnt + 16'd1;
                    end
                end

                default: tx_state <= TX_IDLE;
            endcase
        end
    end

    // -------------------------------------------------------------
    // 6. CPU Register Read Bus Interface
    // -------------------------------------------------------------
    wire [31:0] status_word = {
        16'd0,
        1'b0, fifo_count, // [14:8] words in FIFO
        5'd0,
        tx_busy,          // bit 2
        (fifo_count == FIFO_DEPTH), // bit 1: full
        (fifo_count > 0)  // bit 0: ready
    };

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            rdata <= 32'd0;
        end else if (req && !we) begin
            case (addr)
                32'hFFFF_FFB0: rdata <= status_word;
                32'hFFFF_FFB1: rdata <= (fifo_count > 0) ? fifo_mem[rd_ptr] : 32'd0;
                default:       rdata <= 32'd0;
            endcase
        end
    end

endmodule

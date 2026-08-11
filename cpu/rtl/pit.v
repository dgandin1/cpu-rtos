module pit (
    input  wire        CLK,
    input  wire        RESET,
    input  wire [31:0] ADDR,       // Address bus from CPU
    input  wire [31:0] DATA_IN,    // Data from CPU (DataB)
    input  wire        MW,         // Memory Write Enable
    output reg         OUT         // Interrupt signal
);

    localparam PIT_ADDR = 32'hFFFF_FFFA; // Sign extended 4090

    reg [31:0] stored_ld_val; // Internal reload register
    reg [31:0] current;       // Active countdown register

    wire write_event;
    assign write_event = MW && (ADDR == PIT_ADDR);

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            stored_ld_val <= 32'd0;
        end else if (write_event) begin
            stored_ld_val <= DATA_IN;
        end
    end

    // 2. Countdown Counter Logic
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            current <= 32'd0;
            OUT     <= 1'b0;
        end else if (write_event) begin
            current <= DATA_IN;
            OUT     <= 1'b0;
        end else if (stored_ld_val == 32'd0) begin
            current <= 32'd0;
            OUT     <= 1'b0;
        end else if (current == 32'd1) begin
            current <= stored_ld_val;
            OUT     <= 1'b1;
        end else begin
            // Normal countdown step
            current <= current - 1'b1;
            OUT     <= 1'b0;
        end
    end

endmodule

module vga_controller (
    input CLK,              // 50 MHz system clock
    input RESET,
    output reg hsync,
    output reg vsync,
    output reg [2:0] rgb,
    output [31:0] vram_addr,
    input [31:0] vram_data
);

    // 0. Clock divider: Generate 25 MHz enable pulse from 100 MHz CLK (divide by 4)
    reg [1:0] clk_div_cnt;
    wire clk_25mhz_en = (clk_div_cnt == 2'b11);
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            clk_div_cnt <= 2'b00;
        end else begin
            clk_div_cnt <= clk_div_cnt + 2'b01;
        end
    end

    // 1. Standard 640x480 @ 60Hz timing counters (25 MHz pixel tick)
    reg [9:0] h_count;
    reg [9:0] v_count;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            h_count <= 0;
            v_count <= 0;
        end else if (clk_25mhz_en) begin
            if (h_count == 799) begin
                h_count <= 0;
                v_count <= (v_count == 524) ? 0 : v_count + 1;
            end else begin
                h_count <= h_count + 1;
            end
        end
    end

    // 2. Sync signals (standard negative polarity)
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            hsync <= 1'b1;
            vsync <= 1'b1;
        end else if (clk_25mhz_en) begin
            hsync <= ~(h_count >= 10'd656 && h_count < 10'd752);
            vsync <= ~(v_count >= 10'd490 && v_count < 10'd492);
        end
    end

    // 3. 7x Hardware Upscaler for 64x64 buffer (448x448 active display area)
    // Horizontal active: 96 to 543 (448 px)
    // Vertical active:   16 to 463 (448 px)
    wire game_active_h = (h_count >= 10'd96 && h_count < 10'd544);
    wire game_active_v = (v_count >= 10'd16 && v_count < 10'd464);
    wire game_active   = game_active_h && game_active_v;

    reg [2:0] h_repeat;
    reg [5:0] game_x;
    reg [2:0] v_repeat;
    reg [5:0] game_y;

    // Horizontal pixel repeater (repeats each 64-grid pixel 7 times)
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            h_repeat <= 3'd0;
            game_x   <= 6'd0;
        end else if (clk_25mhz_en) begin
            if (h_count == 10'd799) begin
                h_repeat <= 3'd0;
                game_x   <= 6'd0;
            end else if (game_active_h) begin
                if (h_repeat == 3'd6) begin
                    h_repeat <= 3'd0;
                    game_x   <= game_x + 6'd1;
                end else begin
                    h_repeat <= h_repeat + 3'd1;
                end
            end else begin
                h_repeat <= 3'd0;
                game_x   <= 6'd0;
            end
        end
    end

    // Vertical line repeater (repeats each 64-grid line 7 times)
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            v_repeat <= 3'd0;
            game_y   <= 6'd0;
        end else if (clk_25mhz_en) begin
            if (h_count == 10'd799 && v_count == 10'd524) begin
                v_repeat <= 3'd0;
                game_y   <= 6'd0;
            end else if (h_count == 10'd799) begin
                if (game_active_v) begin
                    if (v_repeat == 3'd6) begin
                        v_repeat <= 3'd0;
                        game_y   <= game_y + 6'd1;
                    end else begin
                        v_repeat <= v_repeat + 3'd1;
                    end
                end else begin
                    v_repeat <= 3'd0;
                    game_y   <= 6'd0;
                end
            end
        end
    end

    // 4. DRAM Address Generator (64 pixels/row = 2 words/row)
    // word_index = (game_y * 2) + (game_x / 32)
    wire [31:0] word_index = {25'd0, game_y, game_x[5]};
    assign vram_addr = 32'd101 + word_index;  

    // 5. 1-cycle pipeline registers matching DRAM synchronous read latency
    reg [4:0] bit_index_d1;
    reg       active_d1;

    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            bit_index_d1 <= 5'd0;
            active_d1    <= 1'b0;
        end else if (clk_25mhz_en) begin
            bit_index_d1 <= game_x[4:0];
            active_d1    <= game_active;
        end
    end

    wire pixel_on = vram_data[bit_index_d1];

    // 6. RGB Output
    always @(posedge CLK or posedge RESET) begin
        if (RESET) begin
            rgb <= 3'b000;
        end else if (clk_25mhz_en) begin
            if (active_d1 && pixel_on) begin
                rgb <= 3'b111;
            end else begin
                rgb <= 3'b000;
            end
        end
    end

endmodule

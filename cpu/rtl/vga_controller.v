module vga_controller (
    input CLK,
    input RESET,
    output reg hsync,
    output reg vsync,
    output reg [2:0] rgb,
    output [31:0] vram_addr,
    input [31:0] vram_data
);

   // reg [1:0] clk_div;
    wire pixel_clk = CLK;
   // always @(posedge CLK) clk_div <= clk_div + 1;

    reg [9:0] h_count;
    reg [9:0] v_count;


    always @(posedge CLK) begin

        if (RESET) begin
            h_count <= 0;
            v_count <= 0;
        end else if (pixel_clk) begin
            if (h_count == 799) begin
                h_count <= 0;
                v_count <= (v_count == 524) ? 0 : v_count + 1;
            end else begin
                h_count <= h_count + 1;
            end
        end

    end

    wire active = (h_count < 640) && (v_count < 480);

    always @(posedge CLK) begin
        if (pixel_clk) begin
            hsync <= ~(h_count >= 656 && h_count < 752);
            vsync <= ~(v_count >= 490 && v_count < 492);
        end
    end

    wire [31:0] word_index = ({22'd0, v_count} * 32'd20) + ({22'd0, h_count} / 32'd32);
    wire [4:0] bit_index = h_count[4:0];

    assign vram_addr = 32'd101 + word_index; // assuming VRAM starts at 101

    wire pixel_on = vram_data[bit_index];

    always @(posedge CLK) begin
        if (active && pixel_on) rgb <= 3'b111;  //pixel on
        else rgb <= 3'b000;                     // pixel off
    end


endmodule

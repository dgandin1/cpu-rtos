module cmod_top (
    input clk_12mhz,
    input [1:0] btn,
    output hsync,
    output vsync,
    output [2:0] rgb
);

    wire CLK;
    wire locked;

    clk_wiz_0 clk_gen (
        .clk_in1(clk_12mhz),
        .clk_out1(CLK),
        .locked(locked)
    );

    wire sys_reset = ~locked | btn[0];

    cpu main_processor (
        .CLK(CLK),
        .RESET(sys_reset),
        .key_w(btn[1]),
        .key_s(1'b0),
        .hsync(hsync),
        .vsync(vsync),
        .rgb(rgb)
    );

endmodule
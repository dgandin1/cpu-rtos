module cmod_top (
    input clk_12mhz,
    input [1:0] btn,
    output hsync,
    output vsync,
    output [2:0] rgb,

    // Physical Cmod A7 ISSI IS61WV5128BLL SRAM Interface
    output [18:0] MemAdr,
    inout  [7:0]  MemDB,
    output        RamCEn,
    output        RamOEn,
    output        RamWEn
);

    wire CLK;
    wire locked;

    clk_wiz_0 clk_gen (
        .clk_in1(clk_12mhz),
        .clk_out1(CLK),
        .locked(locked)
    );

    wire sys_reset = ~locked | btn[0];

    wire debounce_button;

    cpu main_processor (
        .CLK(CLK),
        .RESET(sys_reset),
        .key_w(debounce_button),
        .key_s(1'b0),
        .hsync(hsync),
        .vsync(vsync),
        .rgb(rgb),
        .MemAdr(MemAdr),
        .MemDB(MemDB),
        .RamCEn(RamCEn),
        .RamOEn(RamOEn),
        .RamWEn(RamWEn)
    );

    btn_debounce u_btn_debounce (
        .clk(CLK),
        .reset(sys_reset),
        .btn_in(btn[1]),
        .btn_pulse(debounce_button)
    );

endmodule


module btn_debounce (
        input  wire clk,
        input  wire reset,
        input  wire btn_in,
        output reg  btn_pulse // 1-clock-cycle pulse on press
    );
        reg [1:0] sync;
        always @(posedge clk) sync <= {sync[0], btn_in};
    
        reg [18:0] count;
        reg state;
        reg state_prev;
    
        always @(posedge clk) begin
            if (reset) begin
                count      <= 19'd0;
                state      <= 1'b0;
                state_prev <= 1'b0;
                btn_pulse  <= 1'b0;
            end else begin
                state_prev <= state;
                btn_pulse  <= (state && !state_prev); // 1-cycle pulse on 0 -> 1
    
                if (sync[1] != state) begin
                    count <= count + 1'b1;
                    if (count == 19'd500_000) begin
                        state <= sync[1];
                        count <= 19'd0;
                    end
                end else begin
                    count <= 19'd0;
                end
            end
        end
endmodule

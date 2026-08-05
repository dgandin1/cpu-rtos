module out_device(OUT_BUFFER, input_char, RESET, CLK, LD);
    
    output reg [8191:0] OUT_BUFFER;
    input [7:0]         input_char;
    input               RESET;
    reg                 pos;
    input               CLK;
    input               LD;

    

    always @(posedge CLK, RESET) begin
        
        if (RESET) begin
            OUT_BUFFER <= 8192'd0;
        end else if (LD) begin
            OUT_BUFFER <= 
        end

        

    end

endmodule
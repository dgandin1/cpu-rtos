module iram(
    input [31:0] FETCH_ADDR,
    output [31:0] INSTRUCTION
);



    reg [31:0] mem [0:255];

    assign INSTRUCTION = mem[FETCH_ADDR];


    initial begin
    $readmemh("program.hex", mem);
    
    // Diagnostic printouts
    $display("--- IRAM LOAD DIAGNOSTIC ---");
    $display("Memory[0] loaded raw hex: %h", mem[0]);
    $display("Memory[1] loaded raw hex: %h", mem[1]);
    $display("Memory[2] loaded raw hex: %h", mem[2]);
    $display("----------------------------");
end

endmodule

module iram #(
    parameter WORDS = 4096 // 4096 x 32-bit words = 16 KB Instruction Memory
)(
    input  wire        CLK,

    // Port A: CPU Instruction Fetch (Zero-wait-state combinational read)
    input  wire [31:0] FETCH_ADDR,
    output wire [31:0] INSTRUCTION,

    // Port B: CPU Memory Stage / Microcontroller Loader (Synchronous Write & Read)
    // Mapped in CPU Data Space at 0x0008_0000 - 0x0008_0FFF
    input  wire        PORT_B_EN,
    input  wire        PORT_B_WE,
    input  wire [31:0] PORT_B_ADDR,
    input  wire [31:0] PORT_B_WDATA,
    output reg  [31:0] PORT_B_RDATA
);

    reg [31:0] mem [0:WORDS-1];

    // Port A: Instruction Fetch
    assign INSTRUCTION = mem[FETCH_ADDR[11:0]];

    // Port B: Data Stage Write / Read
    always @(posedge CLK) begin
        if (PORT_B_EN) begin
            if (PORT_B_WE) begin
                mem[PORT_B_ADDR[11:0]] <= PORT_B_WDATA;
            end
            PORT_B_RDATA <= mem[PORT_B_ADDR[11:0]];
        end
    end

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

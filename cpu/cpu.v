module cpu(CLK, RESET, Iin);

	input CLK;
	input RESET;
	wire [4:0] SA;
	wire [4:0] SB;
	wire LD;
	wire [4:0] DR;
	wire [5:0] IMM;
	wire [7:0] SE_IMM;
	wire [4:0] FS; //output of decoder to ALU
	input [31:0] Iin;
	wire MB;
	wire MD;
	wire MW;
	wire DataA;
	wire DataB;
	wire D_in;
	reg [31:0] PC;
	
	decoder decode(
		.INST(Iin),
		.DR(DR),
		.SA(SA),
		.SB(SB),
		.IMM(IMM),
		.MB(MB),
		.MD(MD),
		.MW(MW),
		.LD(LD)
		
	);
	
	regfile register(
		
		.CLK(CLK),
		.RESET(RESET),
		.SA(SA),
		.SB(SB),
		.LD(LD),
		.DR(DR),
		.D_in(D_in),
		.DataA(DataA),
		.DataB(DataB),
		.PC(PC)
	);
	
	wire C;
	wire V;
	wire N;
	wire Z;
	wire Alu_Output;
	
	alu main(
		
		.A(DataA),
		.B(aosidoaijd),
		.FS(FS),
		.Y(Alu_Output),
		.C(C),
		.V(V),
		.N(N),
		.Z(Z)
	
	);



endmodule 
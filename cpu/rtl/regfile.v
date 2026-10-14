module regfile(CLK, RESET, SA, SB, LD, DR, D_in, DataA, DataB);
	input CLK, RESET;
	input [4:0] SA, SB;
	output [31:0] DataA, DataB;
	input LD;
	input [4:0] DR;
	input [31:0] D_in;
	
	reg [31:0] storage [31:0];
	
	// For Fowarding
	assign DataA = (SA == 5'd0) ? 32'd0 :
	               (LD && (DR == SA)) ? D_in : storage[SA];
	assign DataB = (SB == 5'd0) ? 32'd0 :
	               (LD && (DR == SB)) ? D_in : storage[SB];
	
	integer i;
	
	always @(posedge CLK) begin
		if (RESET)
			for (i = 0; i < 32; i = i + 1)
				storage[i] <= 32'd0;
		else if (LD && DR != 5'd0)
			storage[DR] <= D_in;
	end



endmodule

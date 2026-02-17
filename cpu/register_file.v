module register_file(CLK, RESET, SA, SB, LD, DR, D_in, DataA, DataB);
	input CLK, RESET;
	input [4:0] SA, SB;
	output [31:0] DataA, DataB;
	input LD;
	input [4:0] DR;
	input [31:0] D_in;
	
	reg [31:0] storage [15:0];
	
	assign DataA = storage[SA];
	assign DataB = storage[SB];
	
	integer i;
	
	always @(posedge CLK) begin
		if (RESET)
			for (i = 0; i < 16; i = i + 1)
				storage[i] <= 32'd0;
		else if (LD)
			storage[DR] <= D_in;
	end



endmodule

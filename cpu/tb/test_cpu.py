import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ClockCycles, Timer, RisingEdge

async def setup_cpu_clock(dut):
    """Helper helper to start the CPU master clock"""
    clock = Clock(dut.CLK, 10, unit="ns")
    cocotb.start_soon(clock.start())

@cocotb.test()
async def test_cpu_initialize_and_reset(dut):
    """CPU Master Test: Verify system reset clears registers"""
    await setup_cpu_clock(dut)
    
    dut.RESET.value = 1
    dut.Iin.value = 0x00000000 # NOP / Clean inputs
    
    await ClockCycles(dut.CLK, 2)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Assert that the internal control signals are calm post-reset
    assert int(dut.decode.LD.value) == 0 or int(dut.decode.LD.value) == 0

@cocotb.test()
async def test_cpu_register_add_instruction(dut):
    """CPU Master Test: Execute a Register-to-Register ADD instruction"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Pre-populate internal registers using cocotb backdoor access for testing
    # Let's manually inject values into Register 1 and Register 2
    dut.register.storage[1].value = 40
    dut.register.storage[2].value = 22
    await FallingEdge(dut.CLK)

    # Craft a mock instruction token for an ADD operation: R3 = R1 + R2
    # NOTE: Modify this binary value depending on how your decoder mapping looks!
    # Let's assume your decoder extracts fields based on your ports:
    # DR=3, SA=1, SB=2, FS=ADD(3'b000), MB=0 (Use Reg), LD=1 (Write back enabled)
    
    # Formulate a dummy 32-bit instruction that your decoder can read:
    # (This is an example layout placeholder; adjust to match your exact decoder.v)
    # Verilog mapping:
    # [31:25] = func7 (0)
    # [24:20] = SB (2)
    # [19:15] = SA (1)
    # [14:12] = func3 (0)
    # [11:7]  = DR (3)
    # [6:0]   = Opcode (0b0110011)

    opcode = 0b0110011
    func3  = 0b000
    func7  = 0b0000000
    dr     = 3
    sa     = 1
    sb     = 2

    mock_instruction = (func7 << 25) | (sb << 20) | (sa << 15) | (func3 << 12) | (dr << 7) | opcode
    
    dut.Iin.value = mock_instruction
    
    # Allow 1 clock cycle for the posedge CLK to capture and write back the data
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # Check if the result (40 + 22 = 62) reached the ALU output and destination reg
    assert dut.Alu_Output.value.to_unsigned() == 62, f"ALU output wrong, got: {dut.Alu_Output.value.to_unsigned()}"
    assert dut.register.storage[3].value.to_unsigned() == 62, "Regfile failed to store the ALU result!"

@cocotb.test()
async def test_cpu_immediate_add_instruction(dut):
    """CPU Master Test: Execute an Immediate ADD instruction (R4 = R1 + IMM)"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    
    # Inject initial state backdoor value
    dut.register.storage[1].value = 100
    await FallingEdge(dut.CLK)
    
    # Craft a mock instruction configuration:
    # DR=4, SA=1, IMM=5, MB=1 (Select Immediate Mux path), LD=1, FS=ADD(3'b000)
    opcode = 0b0010011
    dr     = 4
    sa     = 1
    imm    = 5

    mock_instruction_imm = (imm << 20) | (sa << 15) | (dr << 7) | opcode
        
    dut.Iin.value = mock_instruction_imm
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # 100 + 5 = 105
    assert dut.Alu_Output.value.to_unsigned() == 105
    assert dut.register.storage[4].value.to_unsigned() == 105

@cocotb.test()
async def test_cpu_register_sub_instruction(dut):
    """CPU Master Test: Execute a Register-to-Register SUB instruction (R3 = R1 - R2)"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Backdoor inject values: R1 = 50, R2 = 15
    dut.register.storage[1].value = 50
    dut.register.storage[2].value = 15
    await FallingEdge(dut.CLK)

    # Verilog mapping for SUB:
    # [31:25] = func7 (7'b0100000)
    # [24:20] = SB (2)
    # [19:15] = SA (1)
    # [14:12] = func3 (3'b000)
    # [11:7]  = DR (3)
    # [6:0]   = Opcode (0b0110011)
    opcode = 0b0110011
    func3  = 0b000
    func7  = 0b0100000 # Critical for SUB distinction
    dr     = 3
    sa     = 1
    sb     = 2

    mock_instruction = (func7 << 25) | (sb << 20) | (sa << 15) | (func3 << 12) | (dr << 7) | opcode
    dut.Iin.value = mock_instruction
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # 50 - 15 = 35
    assert dut.Alu_Output.value.to_unsigned() == 35, f"ALU subtraction failed, got: {dut.Alu_Output.value.to_unsigned()}"
    assert dut.register.storage[3].value.to_unsigned() == 35, "Regfile failed to store SUB result!"


@cocotb.test()
async def test_cpu_register_and_instruction(dut):
    """CPU Master Test: Execute a Register-to-Register AND instruction (R5 = R1 & R2)"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Backdoor inject bitwise values: R1 = 0b1100 (12), R2 = 0b1010 (10)
    dut.register.storage[1].value = 12
    dut.register.storage[2].value = 10
    await FallingEdge(dut.CLK)

    # Verilog mapping for AND: func3 = 3'b111
    opcode = 0b0110011
    func3  = 0b111
    func7  = 0b0000000
    dr     = 5
    sa     = 1
    sb     = 2

    mock_instruction = (func7 << 25) | (sb << 20) | (sa << 15) | (func3 << 12) | (dr << 7) | opcode
    dut.Iin.value = mock_instruction
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # 12 & 10 = 8 (0b1000)
    assert dut.Alu_Output.value.to_unsigned() == 8, f"ALU AND failed, got: {dut.Alu_Output.value.to_unsigned()}"
    assert dut.register.storage[5].value.to_unsigned() == 8


@cocotb.test()
async def test_cpu_register_or_instruction(dut):
    """CPU Master Test: Execute a Register-to-Register OR instruction (R6 = R1 | R2)"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Backdoor inject bitwise values: R1 = 0b1100 (12), R2 = 0b1010 (10)
    dut.register.storage[1].value = 12
    dut.register.storage[2].value = 10
    await FallingEdge(dut.CLK)

    # Verilog mapping for OR: func3 = 3'b110
    opcode = 0b0110011
    func3  = 0b110
    func7  = 0b0000000
    dr     = 6
    sa     = 1
    sb     = 2

    mock_instruction = (func7 << 25) | (sb << 20) | (sa << 15) | (func3 << 12) | (dr << 7) | opcode
    dut.Iin.value = mock_instruction
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # 12 | 10 = 14 (0b1110)
    assert dut.Alu_Output.value.to_unsigned() == 14, f"ALU OR failed, got: {dut.Alu_Output.value.to_unsigned()}"
    assert dut.register.storage[6].value.to_unsigned() == 14


@cocotb.test()
async def test_cpu_register_xor_instruction(dut):
    """CPU Master Test: Execute a Register-to-Register XOR instruction (R7 = R1 ^ R2)"""
    await setup_cpu_clock(dut)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Backdoor inject bitwise values: R1 = 0b1100 (12), R2 = 0b1010 (10)
    dut.register.storage[1].value = 12
    dut.register.storage[2].value = 10
    await FallingEdge(dut.CLK)

    # Verilog mapping for XOR: func3 = 3'b100 (Assuming Verilog bugfix)
    opcode = 0b0110011
    func3  = 0b100
    func7  = 0b0000000
    dr     = 7
    sa     = 1
    sb     = 2

    mock_instruction = (func7 << 25) | (sb << 20) | (sa << 15) | (func3 << 12) | (dr << 7) | opcode
    dut.Iin.value = mock_instruction
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # 12 ^ 10 = 6 (0b0110)
    assert dut.Alu_Output.value.to_unsigned() == 6, f"ALU XOR failed, got: {dut.Alu_Output.value.to_unsigned()}"
    assert dut.register.storage[7].value.to_unsigned() == 6

@cocotb.test()
async def test_cpu_with_program_counter_and_iram(dut):
    """CPU Master Test: Verify PC increments and drives IRAM fetching correctly"""
    
    # 1. Start the master clock
    await setup_cpu_clock(dut)
    
    # 2. Trigger a hardware reset to clear the Program Counter to 0
    dut.RESET.value = 1
    await ClockCycles(dut.CLK, 2)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # 3. Load a mini-program directly into your IRAM's internal memory array
    # Let's assume you fixed your Verilog decoder's IMM size to 12-bits (or adjusted accordingly)
    
    # Instruction 0: addi r1, r0, 10  -> R1 = 10 (Opcode: 0010011, dr=1, sa=0, imm=10)
    # Binary: 000000001010 00000 000 00001 0010011 -> 0x00A00093
    dut.instruction_memory.mem[0].value = 0x00A00093
    
    # Instruction 1: addi r2, r0, 5   -> R2 = 5  (Opcode: 0010011, dr=2, sa=0, imm=5)
    # Binary: 000000000101 00000 000 00010 0010011 -> 0x00500113
    dut.instruction_memory.mem[1].value = 0x00500113
    
    # Instruction 2: add r3, r1, r2   -> R3 = R1 + R2 (Opcode: 0110011, dr=3, sa=1, sb=2)
    # Binary: 0000000 00010 00001 000 00011 0110011 -> 0x002081B3
    dut.instruction_memory.mem[2].value = 0x002081B3

    # 4. Step through Cycle 1 (Fetch & Execute Instruction 0)
    # At this point, PC should be 0. Let's check if the decoder sees the first instruction.
    assert dut.program_counter.PC.value.to_unsigned() == 0, "PC did not start at 0!"
    
    # Wait for the clock edge to process the instruction execution
    await ClockCycles(dut.CLK, 1) 
    await FallingEdge(dut.CLK)
    
    # Verify that the decoder registered the ADDI properties
    assert int(dut.decode.LD.value) == 1, "Load enable should be active for ADDI"
    assert int(dut.decode.MB.value) == 1, "MB mux should select Immediate path for ADDI"

    # 5. Step through Cycle 2 (Fetch & Execute Instruction 1)
    # The PC should have automatically updated to 1
    assert dut.program_counter.PC.value.to_unsigned() == 1, f"PC failed to increment to 1, got {dut.program_counter.PC.value.to_unsigned()}"
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)

    # 6. Step through Cycle 3 (Fetch & Execute Instruction 2)
    # The PC should now be 2, pulling the R-type ADD instruction
    assert dut.program_counter.PC.value.to_unsigned() == 2
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # Verify the decoder successfully shifted gears back to an R-Type instruction style
    assert int(dut.decode.MB.value) == 0, "MB mux should select Register path for ADD"
    assert int(dut.decode.FS.value) == 0, "ALU function selection should be ADD (3'b000)"
    
    # Optional: If your register file updates synchronously, check your register outcomes
    # assert dut.register.storage[3].value.to_unsigned() == 15
    assert dut.register.storage[3].value.to_unsigned() == 15

@cocotb.test()
async def test_cpu_load_and_store_word(dut):
    """CPU Master Test: Verify sw saves to DRAM and lw reads it back cleanly"""
    
    # 1. Start the master clock
    await setup_cpu_clock(dut)
    
    # 2. Reset the system
    dut.RESET.value = 1
    await ClockCycles(dut.CLK, 2)
    
    # Drop reset on a falling edge so it is stable before the next posedge
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    await Timer(1, unit="ps") # Let values propagate combinationally
    
    # 3. Pre-populate register 5 with test data using backdoor access
    test_data = 0xDEADBEEF
    dut.register.storage[5].value = test_data
    dut.register.storage[6].value = 0

    # 4. Compile and inject instructions into IRAM
    # Instruction 0: sw r5, 4(r0) -> Corrected Hex
    dut.instruction_memory.mem[0].value = 0x004022A3
    
    # Instruction 1: lw r6, 4(r0) -> Corrected Hex
    dut.instruction_memory.mem[1].value = 0x00402303
    await Timer(1, unit="ps")

    # 5. Execute Instruction 0: STORE WORD (sw)
    assert dut.program_counter.PC.value.to_unsigned() == 0
    
    # Print out diagnostic info to find the zero
    print(f"--- DEBUG SW STEP ---")
    print(f"Decoder SB: {dut.decode.SB.value.to_unsigned()}") # Should be 5
    print(f"Register DataB: {hex(dut.register.DataB.value.to_unsigned())}") # Should be 0xDEADBEEF
    print(f"ALU Input A: {dut.main.A.value.to_unsigned()}") # Should be 0 (R0)
    print(f"ALU Input B: {dut.main.B.value.to_unsigned()}") # Should be 4 (SE_IMM)
    print(f"ALU Output (ADDR): {dut.main.Y.value.to_unsigned()}") # Should be 4
    print(f"DRAM Data In: {hex(dut.data_memory.DATA_IN.value.to_unsigned())}")
    print(f"---------------------")

    assert int(dut.decode.MW.value) == 1
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)

    # 6. Execute Instruction 1: LOAD WORD (lw)
    assert dut.program_counter.PC.value.to_unsigned() == 1
    
    # --- CHECK DECODER NOW ---
    assert int(dut.decode.MW.value) == 0, "Memory Write (MW) should be disabled during LW"
    assert int(dut.decode.MD.value) == 1, "Memory Destination (MD) mux should select DRAM path"
    assert int(dut.decode.LD.value) == 1, "Register Writeback (LD) should be enabled during LW"
    
    # Print out diagnostic info for LW step
    print(f"--- DEBUG LW STEP ---")
    print(f"Decoder DR: {dut.decode.DR.value.to_unsigned()}") # Should be 6
    print(f"Decoder SA: {dut.decode.SA.value.to_unsigned()}") # Should be 0
    print(f"ALU Output (ADDR): {dut.main.Y.value.to_unsigned()}") # Should be 4
    print(f"DRAM Data Out: {hex(dut.data_memory.DATA_OUT.value.to_unsigned())}") # Should be 0xDEADBEEF
    print(f"Mux MD Output (D_in): {hex(dut.D_in.value.to_unsigned())}") # Should be 0xDEADBEEF
    print(f"---------------------")

    # Pulse the clock to let the Register File capture the DRAM data
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)

@cocotb.test()
async def test_cpu_branch_equal(dut):
    """CPU Master Test: Verify BEQ jumps over an instruction when registers are equal"""
    
    await setup_cpu_clock(dut)
    
    # Reset
    dut.RESET.value = 1
    await ClockCycles(dut.CLK, 2)
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    await Timer(1, unit="ps")

    # Set r1 = 10, r2 = 10 (Making them equal so BEQ takes the branch)
    dut.register.storage[1].value = 10
    dut.register.storage[2].value = 10
    dut.register.storage[3].value = 0 # Target register to make sure we skip a write
    await Timer(1, unit="ps")

    # Instruction 0: beq r1, r2, 2 -> If equal, PC = PC + 2 (Jumps from 0 to 2, skipping index 1)
    # Opcode: 1100011, func3: 000, sa: 1, sb: 2, imm: 2
    # Binary: 000000000010_00001_000_00010_1100011 -> 0x00208163
    dut.instruction_memory.mem[0].value = 0x00208163
    
    # Instruction 1: addi r3, r0, 999 (TRAP INSTRUCTION - should be skipped!)
    dut.instruction_memory.mem[1].value = 0x3E700193
    
    # Instruction 2: addi r3, r0, 5 (The destination landing pad)
    dut.instruction_memory.mem[2].value = 0x00500193

    # Cycle 0: Evaluate BEQ at PC=0
    assert dut.program_counter.PC.value.to_unsigned() == 0
    
    # Let the posedge clock execute the branch calculation
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # Verify that the PC completely bypassed index 1 and jumped straight to 2!
    current_pc = dut.program_counter.PC.value.to_unsigned()
    assert current_pc == 2, f"Branch failed! Expected PC=2, but got PC={current_pc}"

    # Cycle 1: Execute landing pad instruction at PC=2
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    await Timer(1, unit="ps")

    # Verify that R3 captured 5 (from instruction 2) and NEVER captured 999
    assert dut.register.storage[3].value.to_unsigned() == 5, \
        f"Trap instruction executed! r3 got {dut.register.storage[3].value.to_unsigned()}"
    
@cocotb.test()
async def test_cpu_software_emulated_left_shift(dut):
    """CPU Test: Verify 1-bit hardwired SLL execution (Software-Driven Shifting)"""
    await setup_cpu_clock(dut)
    
    # 1. Clear out instruction memory slots completely
    for i in range(len(dut.instruction_memory.mem)):
        dut.instruction_memory.mem[i].value = 0x00000013 # NOP

    # 2. Inject SLL Instruction explicitly at address 0
    dut.instruction_memory.mem[0].value = 0x001191B3

    # 3. CRITICAL: Clamp RESET high to freeze the CPU PC at 0
    dut.RESET.value = 1
    await ClockCycles(dut.CLK, 2) # Let the reset clear internal pipeline lines

    # 4. Initialize your data registers WHILE the CPU is frozen in reset
    dut.register.storage[3].value = 5
    dut.register.storage[1].value = 1
    
    # Let the values settle combinationally onto the internal wires
    await Timer(5, unit="ns") 

    # 5. Release RESET on a falling edge so we can sample PC=0 safely
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    
    # Give the ALU output exactly 1 ns of raw simulation time to stabilize 
    # BEFORE any new rising clock edge occurs
    await Timer(1, unit="ns") 

    # Diagnostics
    current_pc = dut.PC_current.value.to_unsigned()
    raw_instruction = dut.Iin.value.to_unsigned()
    current_alu_out = dut.main.Y.value.to_unsigned()

    dut._log.info(f"PC Value: {current_pc}")
    dut._log.info(f"Instruction on Wire: {hex(raw_instruction)}")
    dut._log.info(f"ALU Input DataA: {dut.register.DataA.value.to_unsigned()}")
    dut._log.info(f"ALU Out: {current_alu_out}")

    # --- THESE WILL NOW PASS AT PC = 0 ---
    assert current_pc == 0, f"PC did not stay at 0! Found {current_pc}"
    assert current_alu_out == 10, f"ALU routing failed! Expected 10 on wire, found {current_alu_out}"

    # 6. Step forward exactly one edge to latch the '10' into register storage
    await RisingEdge(dut.CLK)
    await Timer(100, unit="ps")

    res = dut.register.storage[3].value.to_unsigned()
    assert res == 10, f"Register File failed to latch! Expected 10, got {res}"
    dut._log.info("Test Passed Perfectly!")
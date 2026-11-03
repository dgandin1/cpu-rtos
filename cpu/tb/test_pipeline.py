import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles

def encode_addi(rd, rs1, imm12):
    opcode = 0b0010011
    func3  = 0b000
    imm    = imm12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rd << 7) | opcode

def encode_add(rd, rs1, rs2):
    opcode = 0b0110011
    func3  = 0b000
    func7  = 0b0000000
    return (func7 << 25) | (rs2 << 20) | (rs1 << 15) | (func3 << 12) | (rd << 7) | opcode

def encode_sub(rd, rs1, rs2):
    opcode = 0b0110011
    func3  = 0b000
    func7  = 0b0100000
    return (func7 << 25) | (rs2 << 20) | (rs1 << 15) | (func3 << 12) | (rd << 7) | opcode

def encode_sw(rs2, rs1, imm12):
    opcode = 0b0100011
    func3  = 0b010
    imm    = imm12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rs2 << 7) | opcode

def encode_lw(rd, rs1, imm12):
    opcode = 0b0000011
    func3  = 0b010
    imm    = imm12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rd << 7) | opcode

def encode_beq(rs1, rs2, offset12):
    opcode = 0b1100011
    func3  = 0b000
    imm    = offset12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rs2 << 7) | opcode

def encode_blt(rs1, rs2, offset12):
    opcode = 0b1100011
    func3  = 0b001
    imm    = offset12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rs2 << 7) | opcode

def encode_mret():
    return 0x00000073

NOP = 0x00000013  # addi x0, x0, 0

async def reset_cpu(dut):
    dut.RESET.value = 1
    dut.key_w.value = 0
    dut.key_s.value = 0
    await ClockCycles(dut.CLK, 2)
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0


@cocotb.test()
async def test_forwarding_and_hazards(dut):
    """Test 1: Basic pipeline forwarding and load-use stall."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.instruction_memory.mem[i].value = NOP

    dut.data_memory.mem[10].value = 85

    dut.instruction_memory.mem[0].value = encode_addi(rd=2, rs1=0, imm12=10)
    dut.instruction_memory.mem[1].value = encode_lw(rd=1, rs1=2, imm12=0)
    dut.instruction_memory.mem[2].value = encode_addi(rd=3, rs1=1, imm12=15)

    await reset_cpu(dut)

    await ClockCycles(dut.CLK, 10)
    await FallingEdge(dut.CLK)

    r1 = int(dut.register.storage[1].value)
    r3 = int(dut.register.storage[3].value)
    assert r1 == 85 and r3 == 100


@cocotb.test()
async def test_branch_flushes(dut):
    """Test 2: Branch taken flushes speculative instructions."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.instruction_memory.mem[i].value = NOP

    dut.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=5)
    dut.instruction_memory.mem[1].value = encode_beq(rs1=1, rs2=1, offset12=3)
    dut.instruction_memory.mem[2].value = encode_addi(rd=2, rs1=0, imm12=99)
    dut.instruction_memory.mem[3].value = encode_addi(rd=3, rs1=0, imm12=99)
    dut.instruction_memory.mem[4].value = encode_addi(rd=4, rs1=0, imm12=42)

    await reset_cpu(dut)

    await ClockCycles(dut.CLK, 12)
    await FallingEdge(dut.CLK)

    r2 = int(dut.register.storage[2].value)
    r3 = int(dut.register.storage[3].value)
    r4 = int(dut.register.storage[4].value)
    assert r2 == 0 and r3 == 0 and r4 == 42


@cocotb.test()
async def test_interrupt_precise_execution_and_mret(dut):
    """Test 3: External IRQ triggers precise interrupt, flushes pipeline, executes ISR, and mret resumes."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.instruction_memory.mem[i].value = NOP

    # Main program:
    # PC=0: r1 = 10
    # PC=1: beq r0, r0, 7  -> Jump over ISR table to PC=8
    # PC=4..6: ISR table (MTVEC is 4!)
    #   PC=4: addi r5, r0, 777   -> ISR body sets r5 = 777
    #   PC=5: addi r6, r26, 0    -> Read MCAUSE (reg 26) into r6
    #   PC=6: mret               -> Return from interrupt!
    # Main code continuation:
    #   PC=8:  addi r1, r1, 10   -> r1 = 20
    #   PC=9:  addi r1, r1, 10   -> r1 = 30
    #   PC=10: addi r1, r1, 10   -> r1 = 40
    #   PC=11: addi r1, r1, 10   -> r1 = 50
    dut.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=10)
    dut.instruction_memory.mem[1].value = encode_beq(rs1=0, rs2=0, offset12=7) # Jump to 1+7 = 8

    # ISR at MTVEC=4
    dut.instruction_memory.mem[4].value = encode_addi(rd=5, rs1=0, imm12=777)
    dut.instruction_memory.mem[5].value = encode_addi(rd=6, rs1=26, imm12=0) # r6 = MCAUSE
    dut.instruction_memory.mem[6].value = encode_mret()

    # Main code at PC=8..11
    dut.instruction_memory.mem[8].value  = encode_addi(rd=1, rs1=1, imm12=10)
    dut.instruction_memory.mem[9].value  = encode_addi(rd=1, rs1=1, imm12=10)
    dut.instruction_memory.mem[10].value = encode_addi(rd=1, rs1=1, imm12=10)
    dut.instruction_memory.mem[11].value = encode_addi(rd=1, rs1=1, imm12=10)

    await reset_cpu(dut)

    # Let main reach PC=8
    await ClockCycles(dut.CLK, 5)
    await FallingEdge(dut.CLK)

    # Trigger key_w interrupt (IRQ_in[1] -> irq_id = 1)
    dut._log.info("Asserting key_w IRQ...")
    dut.key_w.value = 1
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    dut.key_w.value = 0

    # Wait for ISR to execute and return to finish main code
    await ClockCycles(dut.CLK, 20)
    await FallingEdge(dut.CLK)

    r1 = int(dut.register.storage[1].value)
    r5 = int(dut.register.storage[5].value)
    r6 = int(dut.register.storage[6].value)

    dut._log.info(f"Interrupt result: r1={r1} (exp 50), r5={r5} (exp 777), r6(MCAUSE)={r6} (exp 1)")
    assert r5 == 777, f"ISR did not execute! r5={r5}"
    assert r6 == 1, f"MCAUSE was wrong! r6={r6}"
    assert r1 == 50, f"Main code did not finish completely! r1={r1}"


@cocotb.test()
async def test_pit_timer_interrupt(dut):
    """Test 4: PIT timer peripheral countdown generates interrupt into pipeline."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.instruction_memory.mem[i].value = NOP

    # PIT_ADDR is 32'hFFFF_FFFA (-6 in decimal)
    # PC=0: r2 = -6 (0xFFA sign extended)
    # PC=1: beq r0, r0, 7  -> Jump to PC=8
    # ISR at PC=4:
    #   PC=4: addi r5, r0, 333  -> ISR ran!
    #   PC=5: addi r6, r26, 0   -> r6 = MCAUSE (expected 3 for timer!)
    #   PC=6: mret
    # Main at PC=8:
    #   PC=8: addi r3, r0, 3    -> reload value = 3 ticks
    #   PC=9: sw   r3, 0(r2)    -> store reload value to PIT peripheral!
    #   PC=10..20: NOPs (waiting for timer interrupt)
    dut.instruction_memory.mem[0].value = encode_addi(rd=2, rs1=0, imm12=-6)
    dut.instruction_memory.mem[1].value = encode_beq(rs1=0, rs2=0, offset12=7)

    # ISR at MTVEC=4
    dut.instruction_memory.mem[4].value = encode_addi(rd=5, rs1=0, imm12=333)
    dut.instruction_memory.mem[5].value = encode_addi(rd=6, rs1=26, imm12=0) # r6 = MCAUSE
    dut.instruction_memory.mem[6].value = encode_mret()

    # Main at PC=8
    dut.instruction_memory.mem[8].value = encode_addi(rd=3, rs1=0, imm12=3)
    dut.instruction_memory.mem[9].value = encode_sw(rs2=3, rs1=2, imm12=0)

    await reset_cpu(dut)

    # Allow time for timer countdown (3 cycles), interrupt fire, ISR execution, and mret
    await ClockCycles(dut.CLK, 25)
    await FallingEdge(dut.CLK)

    r5 = int(dut.register.storage[5].value)
    r6 = int(dut.register.storage[6].value)

    dut._log.info(f"PIT Timer IRQ result: r5={r5} (exp 333), r6(MCAUSE)={r6} (exp 3)")
    assert r5 == 333, f"Timer ISR did not run! r5={r5}"
    assert r6 == 3, f"Timer MCAUSE expected 3, got {r6}"


@cocotb.test()
async def test_interrupt_during_branch_bubble(dut):
    """Test 5: IRQ arriving in bubble cycle immediately after a taken branch captures correct target MEPC, not 0."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.instruction_memory.mem[i].value = NOP

    # PC=0: addi r1, r0, 100
    # PC=1: beq  r0, r0, 10   -> Branches to PC = 1 + 10 = 11
    # PC=2: addi r1, r0, 999  -> Speculative (should be flushed)
    # ISR at MTVEC=4:
    #   PC=4: addi r5, r27, 0   -> r5 = MEPC (should be 11, NOT 0!)
    #   PC=5: mret
    # Target at PC=11:
    #   PC=11: addi r2, r0, 222 -> Target executed
    dut.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=100)
    dut.instruction_memory.mem[1].value = encode_beq(rs1=0, rs2=0, offset12=10)
    dut.instruction_memory.mem[2].value = encode_addi(rd=1, rs1=0, imm12=999)

    dut.instruction_memory.mem[4].value = encode_addi(rd=5, rs1=27, imm12=0)  # r5 = MEPC
    dut.instruction_memory.mem[5].value = encode_mret()

    dut.instruction_memory.mem[11].value = encode_addi(rd=2, rs1=0, imm12=222)

    await reset_cpu(dut)

    # Cycle 0: PC=0 fetch
    # Cycle 1: PC=1 fetch (PC=0 in ID)
    # Cycle 2: PC=2 fetch (PC=1 in ID)
    # Cycle 3: PC=1 in EX (branch resolves and redirects to 11). if_id is flushed.
    # Cycle 4: PC=11 in IF. if_id is flushed bubble (if_id_valid=0).
    # Trigger IRQ exactly here at Cycle 3/4!
    await ClockCycles(dut.CLK, 3)
    await FallingEdge(dut.CLK)
    dut.key_w.value = 1
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    dut.key_w.value = 0

    await ClockCycles(dut.CLK, 20)
    await FallingEdge(dut.CLK)

    r1 = int(dut.register.storage[1].value)
    r2 = int(dut.register.storage[2].value)
    r5 = int(dut.register.storage[5].value)

    dut._log.info(f"Branch-bubble IRQ result: r1={r1} (exp 100), r2={r2} (exp 222), r5(MEPC)={r5} (exp 11)")
    assert r5 == 11, f"MEPC was wrong! Expected 11, got {r5}"
    assert r2 == 222, f"Branch target at PC=11 did not execute! r2={r2}"
    assert r1 == 100, f"r1 was corrupted or reset! r1={r1}"


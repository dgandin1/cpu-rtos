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

NOP = 0x00000013  # addi x0, x0, 0

async def hold_in_reset(dut):
    dut.RESET.value = 1
    dut.key_w.value = 0
    dut.key_s.value = 0
    await ClockCycles(dut.CLK, 3)
    await FallingEdge(dut.CLK)

async def release_reset(dut):
    await ClockCycles(dut.CLK, 2)
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)


@cocotb.test()
async def test_cache_write_through(dut):
    """Test 1: Store word to cached SRAM (addr >= 1000) writes through to physical SRAM."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.u_cpu.instruction_memory.mem[i].value = NOP

    dut.u_cpu.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=1024)
    dut.u_cpu.instruction_memory.mem[1].value = encode_addi(rd=2, rs1=0, imm12=85)
    dut.u_cpu.instruction_memory.mem[2].value = encode_sw(rs2=2, rs1=1, imm12=0)

    await hold_in_reset(dut)
    await release_reset(dut)

    await ClockCycles(dut.CLK, 30)
    await FallingEdge(dut.CLK)

    b0 = int(dut.u_sram.mem[4096].value)
    b1 = int(dut.u_sram.mem[4097].value)
    b2 = int(dut.u_sram.mem[4098].value)
    b3 = int(dut.u_sram.mem[4099].value)
    dut._log.info(f"SRAM @ 4096..4099: {b0:02x} {b1:02x} {b2:02x} {b3:02x}")
    assert b0 == 85, f"Expected 85 at SRAM[4096], got {b0}"
    assert b1 == 0 and b2 == 0 and b3 == 0


@cocotb.test()
async def test_cache_cold_miss_and_refill(dut):
    """Test 2: Cold read miss freezes pipeline, fetches 16 bytes from SRAM, and returns loaded value."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.u_cpu.instruction_memory.mem[i].value = NOP

    dut.u_cpu.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=1040)
    dut.u_cpu.instruction_memory.mem[1].value = encode_lw(rd=3, rs1=1, imm12=0)
    dut.u_cpu.instruction_memory.mem[2].value = encode_addi(rd=4, rs1=3, imm12=1)

    await hold_in_reset(dut)

    # Preload SRAM at Word 1040 (Physical byte: 1040 * 4 = 4160): 0x11223344 (LE: 44 33 22 11)
    dut.u_sram.mem[4160].value = 0x44
    dut.u_sram.mem[4161].value = 0x33
    dut.u_sram.mem[4162].value = 0x22
    dut.u_sram.mem[4163].value = 0x11

    # Word 1 (1041, Physical byte: 1041 * 4 = 4164): 0x55667788
    dut.u_sram.mem[4164].value = 0x88
    dut.u_sram.mem[4165].value = 0x77
    dut.u_sram.mem[4166].value = 0x66
    dut.u_sram.mem[4167].value = 0x55

    await release_reset(dut)

    stall_observed = False
    for cyc in range(90):
        await FallingEdge(dut.CLK)
        if int(dut.u_cpu.cache_stall.value) == 1:
            stall_observed = True
        r3 = int(dut.u_cpu.register.storage[3].value)
        r4 = int(dut.u_cpu.register.storage[4].value)
        if r3 == 0x11223344 and r4 == 0x11223345:
            break

    r3 = int(dut.u_cpu.register.storage[3].value)
    r4 = int(dut.u_cpu.register.storage[4].value)
    dut._log.info(f"Cold miss results: r3=0x{r3:08x}, r4=0x{r4:08x}, stall_observed={stall_observed}")
    assert stall_observed, "Expected pipeline stall during cold read miss!"
    assert r3 == 0x11223344, f"Expected r3=0x11223344, got 0x{r3:08x}"
    assert r4 == 0x11223345, f"Expected r4=0x11223345, got 0x{r4:08x}"


@cocotb.test()
async def test_cache_read_hit_single_cycle(dut):
    """Test 3: Reading a pre-cached address completes with true 1-cycle latency (0 wait states)."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.u_cpu.instruction_memory.mem[i].value = NOP

    dut.u_cpu.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=1024)
    dut.u_cpu.instruction_memory.mem[1].value = encode_addi(rd=2, rs1=0, imm12=42)
    dut.u_cpu.instruction_memory.mem[2].value = encode_sw(rs2=2, rs1=1, imm12=0)
    dut.u_cpu.instruction_memory.mem[3].value = encode_lw(rd=3, rs1=1, imm12=0)
    dut.u_cpu.instruction_memory.mem[4].value = encode_lw(rd=5, rs1=1, imm12=0)
    dut.u_cpu.instruction_memory.mem[5].value = encode_addi(rd=6, rs1=5, imm12=10)

    await hold_in_reset(dut)
    await release_reset(dut)

    # Run until first load completes
    for cyc in range(75):
        await FallingEdge(dut.CLK)
        if int(dut.u_cpu.register.storage[3].value) == 42:
            dut._log.info(f"First load completed at cycle {cyc}")
            break

    # Now observe the second load: it must hit with cache_stall == 0!
    hit_stall_cycles = 0
    for cyc in range(10):
        await FallingEdge(dut.CLK)
        stall = int(dut.u_cpu.cache_stall.value)
        r5 = int(dut.u_cpu.register.storage[5].value)
        if stall == 1:
            hit_stall_cycles += 1
        if r5 == 42:
            dut._log.info(f"Second load hit completed at sub-cycle {cyc} with r5=42")
            break

    await ClockCycles(dut.CLK, 2)
    await FallingEdge(dut.CLK)

    r5 = int(dut.u_cpu.register.storage[5].value)
    r6 = int(dut.u_cpu.register.storage[6].value)
    dut._log.info(f"Read hit results: r5={r5}, r6={r6}, hit_stall_cycles={hit_stall_cycles}")
    assert r5 == 42, f"Expected r5=42, got {r5}"
    assert r6 == 52, f"Expected r6=52, got {r6}"
    assert hit_stall_cycles == 0, f"Cache read hit stalled {hit_stall_cycles} cycles! Expected 0."


@cocotb.test()
async def test_cache_spatial_locality(dut):
    """Test 4: Refilling line 1056 brings all 4 words (1056, 1057, 1058, 1059) into cache; subsequent words hit with 0 stalls."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.u_cpu.instruction_memory.mem[i].value = NOP

    dut.u_cpu.instruction_memory.mem[0].value = encode_addi(rd=1, rs1=0, imm12=1056)
    dut.u_cpu.instruction_memory.mem[1].value = encode_lw(rd=2, rs1=1, imm12=0)
    dut.u_cpu.instruction_memory.mem[2].value = encode_lw(rd=3, rs1=1, imm12=1)
    dut.u_cpu.instruction_memory.mem[3].value = encode_lw(rd=4, rs1=1, imm12=2)
    dut.u_cpu.instruction_memory.mem[4].value = encode_lw(rd=5, rs1=1, imm12=3)

    await hold_in_reset(dut)

    # Preload the 4 words of line 1056 in SRAM (Physical bytes 4224..4239)
    dut.u_sram.mem[4224].value = 100
    dut.u_sram.mem[4225].value = 0
    dut.u_sram.mem[4226].value = 0
    dut.u_sram.mem[4227].value = 0

    dut.u_sram.mem[4228].value = 200
    dut.u_sram.mem[4229].value = 0
    dut.u_sram.mem[4230].value = 0
    dut.u_sram.mem[4231].value = 0

    dut.u_sram.mem[4232].value = 50
    dut.u_sram.mem[4233].value = 0
    dut.u_sram.mem[4234].value = 0
    dut.u_sram.mem[4235].value = 0

    dut.u_sram.mem[4236].value = 75
    dut.u_sram.mem[4237].value = 0
    dut.u_sram.mem[4238].value = 0
    dut.u_sram.mem[4239].value = 0

    await release_reset(dut)

    # Wait for first load to finish (miss & refill)
    for cyc in range(75):
        await FallingEdge(dut.CLK)
        if int(dut.u_cpu.register.storage[2].value) == 100:
            dut._log.info(f"Line 1056 refill completed at cycle {cyc}")
            break

    # Now observe words 1, 2, 3: they should all hit with 0 stall cycles!
    subsequent_stalls = 0
    for cyc in range(15):
        await FallingEdge(dut.CLK)
        if int(dut.u_cpu.cache_stall.value) == 1:
            subsequent_stalls += 1
        r5 = int(dut.u_cpu.register.storage[5].value)
        if r5 == 75:
            break

    await ClockCycles(dut.CLK, 3)
    await FallingEdge(dut.CLK)

    r2 = int(dut.u_cpu.register.storage[2].value)
    r3 = int(dut.u_cpu.register.storage[3].value)
    r4 = int(dut.u_cpu.register.storage[4].value)
    r5 = int(dut.u_cpu.register.storage[5].value)
    dut._log.info(f"Spatial locality: r2={r2}, r3={r3}, r4={r4}, r5={r5}, subsequent_stalls={subsequent_stalls}")
    assert r2 == 100, f"Expected r2=100, got {r2}"
    assert r3 == 200, f"Expected r3=200, got {r3}"
    assert r4 == 50,  f"Expected r4=50, got {r4}"
    assert r5 == 75,  f"Expected r5=75, got {r5}"
    assert subsequent_stalls == 0, f"Spatial locality hits stalled {subsequent_stalls} cycles! Expected 0."


@cocotb.test()
async def test_cache_eviction_and_replacement(dut):
    """Test 5: Conflicting lines (same index, different tag) evict and re-fetch from SRAM accurately."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(1024):
        dut.u_cpu.instruction_memory.mem[i].value = NOP

    # Addr A = 1024 (line index 256)
    # Addr B = 1024 + 8192 = 9216 (same line index 256, tag differs by 1)
    dut.u_cpu.instruction_memory.mem[0].value  = encode_addi(rd=1, rs1=0, imm12=1024)
    dut.u_cpu.instruction_memory.mem[1].value  = encode_addi(rd=11, rs1=0, imm12=1024)
    dut.u_cpu.instruction_memory.mem[2].value  = encode_add(rd=11, rs1=11, rs2=11) # 2048
    dut.u_cpu.instruction_memory.mem[3].value  = encode_add(rd=11, rs1=11, rs2=11) # 4096
    dut.u_cpu.instruction_memory.mem[4].value  = encode_add(rd=11, rs1=11, rs2=11) # 8192
    dut.u_cpu.instruction_memory.mem[5].value  = encode_add(rd=10, rs1=1, rs2=11)  # 9216
    dut.u_cpu.instruction_memory.mem[6].value  = encode_addi(rd=2, rs1=0, imm12=77)
    dut.u_cpu.instruction_memory.mem[7].value  = encode_addi(rd=3, rs1=0, imm12=99)
    dut.u_cpu.instruction_memory.mem[8].value  = encode_sw(rs2=2, rs1=1, imm12=0)   # Store 77 to 1024
    dut.u_cpu.instruction_memory.mem[9].value  = encode_sw(rs2=3, rs1=10, imm12=0)  # Store 99 to 9216
    dut.u_cpu.instruction_memory.mem[10].value = encode_lw(rd=20, rs1=10, imm12=0) # Load 9216 -> should get 99
    dut.u_cpu.instruction_memory.mem[11].value = encode_lw(rd=21, rs1=1, imm12=0)  # Load 1024 -> evicted, refetches 77!

    await hold_in_reset(dut)
    await release_reset(dut)

    for cyc in range(300):
        await FallingEdge(dut.CLK)
        r20 = int(dut.u_cpu.register.storage[20].value)
        r21 = int(dut.u_cpu.register.storage[21].value)
        if r20 == 99 and r21 == 77:
            dut._log.info(f"Eviction & replacement verified at cycle {cyc}")
            break

    r20 = int(dut.u_cpu.register.storage[20].value)
    r21 = int(dut.u_cpu.register.storage[21].value)
    dut._log.info(f"Eviction test results: r20={r20} (exp 99), r21={r21} (exp 77)")
    assert r20 == 99, f"Expected r20=99, got {r20}"
    assert r21 == 77, f"Expected r21=77, got {r21}"

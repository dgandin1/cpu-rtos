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

def encode_beq(rs1, rs2, offset12):
    opcode = 0b1100011
    func3  = 0b000
    imm    = offset12 & 0xFFF
    return (imm << 20) | (rs1 << 15) | (func3 << 12) | (rs2 << 7) | opcode

NOP = 0x00000013  # addi x0, x0, 0
CLKS_PER_BIT = 868

async def reset_cpu(dut):
    dut.RESET.value = 1
    dut.key_w.value = 0
    dut.key_s.value = 0
    dut.mcu_rx.value = 1
    await ClockCycles(dut.CLK, 5)
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0

async def send_uart_byte(dut, byte_val):
    # Start bit
    dut.mcu_rx.value = 0
    await ClockCycles(dut.CLK, CLKS_PER_BIT)
    # 8 data bits (LSB first)
    for i in range(8):
        dut.mcu_rx.value = (byte_val >> i) & 1
        await ClockCycles(dut.CLK, CLKS_PER_BIT)
    # Stop bit
    dut.mcu_rx.value = 1
    await ClockCycles(dut.CLK, CLKS_PER_BIT)

async def send_uart_word32(dut, word32):
    # Send 4 bytes in Little Endian order
    for i in range(4):
        b = (word32 >> (i * 8)) & 0xFF
        await send_uart_byte(dut, b)

@cocotb.test()
async def test_iram_port_b_store_and_load(dut):
    """Test 1: CPU stores data/instructions to IRAM Port B (0x0008_0000) and loads it back."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(512):
        dut.instruction_memory.mem[i].value = NOP

    # Put IRAM base address (0x0008_0000) into DRAM[10]
    dut.data_memory.mem[10].value = 0x00080000

    # Program:
    # 0: lw r10, 10(x0)  -> r10 = 0x0008_0000 (IRAM Port B base)
    # 1: addi r1, x0, 777
    # 2: addi r4, x0, 999
    # 3: sw   r1, 20(r10) -> Store 777 to IRAM word 20 (address 0x0008_0014)
    # 4: sw   r4, 21(r10) -> Store 999 to IRAM word 21 (address 0x0008_0015)
    # 5: lw   r2, 20(r10) -> Load from IRAM word 20 into r2
    # 6: lw   r3, 21(r10) -> Load from IRAM word 21 into r3
    dut.instruction_memory.mem[0].value = encode_lw(rd=10, rs1=0, imm12=10)
    dut.instruction_memory.mem[1].value = encode_addi(rd=1, rs1=0, imm12=777)
    dut.instruction_memory.mem[2].value = encode_addi(rd=4, rs1=0, imm12=999)
    dut.instruction_memory.mem[3].value = encode_sw(rs2=1, rs1=10, imm12=20)
    dut.instruction_memory.mem[4].value = encode_sw(rs2=4, rs1=10, imm12=21)
    dut.instruction_memory.mem[5].value = encode_lw(rd=2, rs1=10, imm12=20)
    dut.instruction_memory.mem[6].value = encode_lw(rd=3, rs1=10, imm12=21)

    await reset_cpu(dut)

    await ClockCycles(dut.CLK, 20)
    await FallingEdge(dut.CLK)

    # Verify BRAM memory array directly updated
    iram_w20 = int(dut.instruction_memory.mem[20].value)
    iram_w21 = int(dut.instruction_memory.mem[21].value)
    dut._log.info(f"IRAM[20] = {iram_w20} (exp 777), IRAM[21] = {iram_w21} (exp 999)")
    assert iram_w20 == 777, f"IRAM[20] expected 777, got {iram_w20}"
    assert iram_w21 == 999, f"IRAM[21] expected 999, got {iram_w21}"

    # Verify CPU registers received the readback
    r2 = int(dut.register.storage[2].value)
    r3 = int(dut.register.storage[3].value)
    dut._log.info(f"r2 = {r2} (exp 777), r3 = {r3} (exp 999)")
    assert r2 == 777, f"Register r2 expected 777, got {r2}"
    assert r3 == 999, f"Register r3 expected 999, got {r3}"

@cocotb.test()
async def test_mcu_disk_uart_rx_and_fifo_read(dut):
    """Test 2: Stream UART bytes into mcu_rx pin, check DISK_STATUS and pop 32-bit words via DISK_DATA."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(512):
        dut.instruction_memory.mem[i].value = NOP

    # CPU Program with Polling Loops:
    # 0: addi r10, x0, -80   -> r10 = 0xFFFF_FFB0 (DISK_STATUS)
    # 1: lw   r1, 0(r10)     -> r1 = DISK_STATUS (bit 0=ready)
    # 2: beq  r1, x0, -1     -> if r1 == 0, poll again at line 1 (offset -1)
    # 3: lw   r2, 1(r10)     -> r2 = DISK_DATA (pop first word: 0xCAFEBABE)
    # 4: lw   r1, 0(r10)     -> poll for second word
    # 5: beq  r1, x0, -1     -> if r1 == 0, poll again at line 4 (offset -1)
    # 6: lw   r3, 1(r10)     -> r3 = DISK_DATA (pop second word: 0x12345678)
    # 7: lw   r4, 0(r10)     -> r4 = DISK_STATUS (empty)
    # 8: beq  x0, x0, 0      -> halt loop
    dut.instruction_memory.mem[0].value = encode_addi(rd=10, rs1=0, imm12=-80)
    dut.instruction_memory.mem[1].value = encode_lw(rd=1, rs1=10, imm12=0)
    dut.instruction_memory.mem[2].value = encode_beq(rs1=1, rs2=0, offset12=-1)
    dut.instruction_memory.mem[3].value = encode_lw(rd=2, rs1=10, imm12=1)
    dut.instruction_memory.mem[4].value = encode_lw(rd=1, rs1=10, imm12=0)
    dut.instruction_memory.mem[5].value = encode_beq(rs1=1, rs2=0, offset12=-1)
    dut.instruction_memory.mem[6].value = encode_lw(rd=3, rs1=10, imm12=1)
    dut.instruction_memory.mem[7].value = encode_lw(rd=4, rs1=10, imm12=0)
    dut.instruction_memory.mem[8].value = encode_beq(rs1=0, rs2=0, offset12=0)

    await reset_cpu(dut)

    # Transmit two 32-bit words over physical UART mcu_rx line:
    dut._log.info("Sending 0xCAFEBABE over UART mcu_rx...")
    await send_uart_word32(dut, 0xCAFEBABE)
    dut._log.info("Sending 0x12345678 over UART mcu_rx...")
    await send_uart_word32(dut, 0x12345678)

    # Allow CPU to pop second word and reach halt loop
    await ClockCycles(dut.CLK, 50)
    await FallingEdge(dut.CLK)

    r2_data1  = int(dut.register.storage[2].value)
    r3_data2  = int(dut.register.storage[3].value)
    r4_status = int(dut.register.storage[4].value)

    dut._log.info(f"Word 1: 0x{r2_data1:08x} (exp 0xCAFEBABE)")
    dut._log.info(f"Word 2: 0x{r3_data2:08x} (exp 0x12345678)")
    dut._log.info(f"Status after pops: 0x{r4_status:08x} (ready: {r4_status & 1})")

    assert r2_data1 == 0xCAFEBABE, f"Expected 0xCAFEBABE, got 0x{r2_data1:08x}"
    assert r3_data2 == 0x12345678, f"Expected 0x12345678, got 0x{r3_data2:08x}"
    assert (r4_status & 1) == 0, "Status bit 0 (ready) should be 0 after popping all words"

@cocotb.test()
async def test_mcu_disk_fifo_flush(dut):
    """Test 3: Writing 1 to DISK_CTRL (0xFFFF_FFB2) flushes FIFO."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(512):
        dut.instruction_memory.mem[i].value = NOP

    # CPU Program with Polling Loop then Flush:
    # 0: addi r10, x0, -80  (0xFFFF_FFB0)
    # 1: lw   r1, 0(r10)
    # 2: beq  r1, x0, -1    (poll until byte arrived)
    # 3: addi r5, x0, 1
    # 4: sw   r5, 2(r10)    (write 1 to 0xFFFF_FFB2 -> DISK_CTRL flush!)
    # 5: lw   r2, 0(r10)    (read DISK_STATUS)
    # 6: beq  x0, x0, 0     (halt)
    dut.instruction_memory.mem[0].value = encode_addi(rd=10, rs1=0, imm12=-80)
    dut.instruction_memory.mem[1].value = encode_lw(rd=1, rs1=10, imm12=0)
    dut.instruction_memory.mem[2].value = encode_beq(rs1=1, rs2=0, offset12=-1)
    dut.instruction_memory.mem[3].value = encode_addi(rd=5, rs1=0, imm12=1)
    dut.instruction_memory.mem[4].value = encode_sw(rs2=5, rs1=10, imm12=2)
    dut.instruction_memory.mem[5].value = encode_lw(rd=2, rs1=10, imm12=0)
    dut.instruction_memory.mem[6].value = encode_beq(rs1=0, rs2=0, offset12=0)

    await reset_cpu(dut)

    # Send 1 word (4 bytes) over UART
    await send_uart_word32(dut, 0x55AA55AA)

    # Allow CPU to execute flush and read back status
    await ClockCycles(dut.CLK, 50)
    await FallingEdge(dut.CLK)

    fifo_cnt = int(dut.disk_controller.fifo_count.value)
    r2_status = int(dut.register.storage[2].value)
    dut._log.info(f"FIFO count after flush: {fifo_cnt} (exp 0), status: 0x{r2_status:08x}")
    assert fifo_cnt == 0, f"Expected FIFO count 0 after flush, got {fifo_cnt}"
    assert (r2_status & 1) == 0, "Expected empty FIFO in status register"

@cocotb.test()
async def test_dynamic_program_loader(dut):
    """Test 4: Microcontroller streams code over UART, CPU loads it into IRAM and branches to execute it."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    for i in range(512):
        dut.instruction_memory.mem[i].value = NOP

    dut.data_memory.mem[10].value = 0x00080000

    # CPU Bootstrap Routine:
    # 0:  lw   r11, 10(x0)    -> r11 = 0x0008_0000 (IRAM base)
    # 1:  addi r10, x0, -80   -> r10 = 0xFFFF_FFB0 (DISK_STATUS)
    # 2:  lw   r1, 0(r10)     -> poll for word 1
    # 3:  beq  r1, x0, -1
    # 4:  lw   r2, 1(r10)     -> pop word 1 (0xFFFF_FFB1)
    # 5:  sw   r2, 50(r11)    -> store word 1 into IRAM word 50
    # 6:  lw   r1, 0(r10)     -> poll for word 2
    # 7:  beq  r1, x0, -1
    # 8:  lw   r2, 1(r10)     -> pop word 2 (0xFFFF_FFB1)
    # 9:  sw   r2, 51(r11)    -> store word 2 into IRAM word 51
    # 10: beq  x0, x0, 40     -> jump to word 50 (PC = 10 + 40 = 50)
    dut.instruction_memory.mem[0].value  = encode_lw(rd=11, rs1=0, imm12=10)
    dut.instruction_memory.mem[1].value  = encode_addi(rd=10, rs1=0, imm12=-80)
    dut.instruction_memory.mem[2].value  = encode_lw(rd=1, rs1=10, imm12=0)
    dut.instruction_memory.mem[3].value  = encode_beq(rs1=1, rs2=0, offset12=-1)
    dut.instruction_memory.mem[4].value  = encode_lw(rd=2, rs1=10, imm12=1)
    dut.instruction_memory.mem[5].value  = encode_sw(rs2=2, rs1=11, imm12=50)
    dut.instruction_memory.mem[6].value  = encode_lw(rd=1, rs1=10, imm12=0)
    dut.instruction_memory.mem[7].value  = encode_beq(rs1=1, rs2=0, offset12=-1)
    dut.instruction_memory.mem[8].value  = encode_lw(rd=2, rs1=10, imm12=1)
    dut.instruction_memory.mem[9].value  = encode_sw(rs2=2, rs1=11, imm12=51)
    dut.instruction_memory.mem[10].value = encode_beq(rs1=0, rs2=0, offset12=40)

    await reset_cpu(dut)

    # MCU sends the two program instructions:
    # Instruction 1: addi r8, x0, 444
    # Instruction 2: beq  x0, x0, 0
    instr1 = encode_addi(rd=8, rs1=0, imm12=444)
    instr2 = encode_beq(rs1=0, rs2=0, offset12=0)

    dut._log.info("Sending dynamic instruction 1 over UART...")
    await send_uart_word32(dut, instr1)
    dut._log.info("Sending dynamic instruction 2 over UART...")
    await send_uart_word32(dut, instr2)

    # Allow CPU to store instructions into IRAM, jump to PC 50, execute, and halt
    await ClockCycles(dut.CLK, 50)
    await FallingEdge(dut.CLK)

    r8_val = int(dut.register.storage[8].value)
    dut._log.info(f"Dynamic execution result: r8 = {r8_val} (exp 444)")
    assert r8_val == 444, f"Expected r8 == 444 from dynamically executed code, got {r8_val}"


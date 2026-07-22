import cocotb
from cocotb.triggers import Timer

# Helper functions to pack instructions
def make_r_type(funct7, rs2, rs1, funct3, rd, opcode=0x33):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def make_i_type(imm, rs1, funct3, rd, opcode=0x13):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

# --- R-TYPE TESTS ---

@cocotb.test()
async def test_add(dut):
    """Test ADD: add x3, x1, x2"""
    dut.INST.value = make_r_type(funct7=0x00, rs2=2, rs1=1, funct3=0, rd=3)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 3
    assert dut.SA.value.to_unsigned() == 1
    assert dut.SB.value.to_unsigned() == 2
    assert int(dut.MB.value) == 0  # Fixed: Single bit uses int()
    assert int(dut.LD.value) == 1  # Fixed: Single bit uses int()
    assert dut.FS.value.to_unsigned() == 0

@cocotb.test()
async def test_sub(dut):
    """Test SUB: sub x5, x10, x11"""
    dut.INST.value = make_r_type(funct7=0x20, rs2=11, rs1=10, funct3=0, rd=5)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 5
    assert dut.SA.value.to_unsigned() == 10
    assert dut.SB.value.to_unsigned() == 11
    assert int(dut.MB.value) == 0  # Fixed: Single bit uses int()
    assert int(dut.LD.value) == 1  # Fixed: Single bit uses int()
    assert dut.FS.value.to_unsigned() == 1

@cocotb.test()
async def test_xor(dut):
    """Test XOR: xor x12, x4, x5"""
    dut.INST.value = make_r_type(funct7=0x00, rs2=5, rs1=4, funct3=4, rd=12)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 12
    assert dut.FS.value.to_unsigned() == 7

@cocotb.test()
async def test_or(dut):
    """Test OR: or x15, x6, x7"""
    dut.INST.value = make_r_type(funct7=0x00, rs2=7, rs1=6, funct3=6, rd=15)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 15
    assert dut.FS.value.to_unsigned() == 6

@cocotb.test()
async def test_and(dut):
    """Test AND: and x20, x8, x9"""
    dut.INST.value = make_r_type(funct7=0x00, rs2=9, rs1=8, funct3=7, rd=20)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 20
    assert dut.FS.value.to_unsigned() == 4


# --- I-TYPE TESTS ---

@cocotb.test()
async def test_addi(dut):
    """Test ADDI: addi x10, x1, 42"""
    dut.INST.value = make_i_type(imm=42, rs1=1, funct3=0, rd=10)
    await Timer(1, unit="ns")
    
    assert dut.DR.value.to_unsigned() == 10
    assert dut.SA.value.to_unsigned() == 1
    assert int(dut.MB.value) == 1  # Fixed: Single bit uses int()
    assert int(dut.LD.value) == 1  # Fixed: Single bit uses int()
    assert dut.FS.value.to_unsigned() == 0
    assert dut.IMM.value.to_unsigned() == 42
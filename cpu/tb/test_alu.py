import cocotb
from cocotb.triggers import Timer

# Define the FS constants
FS_ADD = 0b000
FS_SUB = 0b001
FS_SRL = 0b010
FS_SLL = 0b011
FS_AND = 0b100
FS_OR  = 0b110

@cocotb.test()
async def test_alu_add(dut):
    """ALU Test: Basic Addition and Zero Flag"""
    dut.A.value = 100
    dut.B.value = 150
    dut.FS.value = FS_ADD
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == 250
    assert int(dut.Z.value) == 0
    assert int(dut.N.value) == 0

@cocotb.test()
async def test_alu_sub(dut):
    """ALU Test: Basic Subtraction and Negative Flag"""
    dut.A.value = 10
    dut.B.value = 20
    dut.FS.value = FS_SUB
    await Timer(1, unit="ns")
    
    # 10 - 20 = -10 (0xFFFFFFF6 in 32-bit Two's Complement)
    assert dut.Y.value.to_unsigned() == 0xFFFFFFF6
    assert int(dut.N.value) == 1  # Result is negative
    assert int(dut.Z.value) == 0

@cocotb.test()
async def test_alu_zero_flag(dut):
    """ALU Test: Equal Subtraction Triggers Zero Flag"""
    dut.A.value = 55
    dut.B.value = 55
    dut.FS.value = FS_SUB
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == 0
    assert int(dut.Z.value) == 1  # Should be high
    assert int(dut.N.value) == 0

@cocotb.test()
async def test_alu_signed_overflow(dut):
    """ALU Test: Signed Overflow (V) Flag Protection"""
    dut.A.value = 2**31 - 1  # Max Positive Signed Int (0x7FFFFFFF)
    dut.B.value = 1
    dut.FS.value = FS_ADD
    await Timer(1, unit="ns")
    
    assert int(dut.V.value) == 1  # Positive + Positive wrapped to Negative
    assert int(dut.C.value) == 0  # No unsigned carry out

@cocotb.test()
async def test_alu_logical_and(dut):
    """ALU Test: Bitwise AND operation"""
    dut.A.value = 0x0F0F0F0F
    dut.B.value = 0x33333333
    dut.FS.value = FS_AND
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == (0x0F0F0F0F & 0x33333333)
    assert int(dut.V.value) == 0  # Overflow must clear on logical ops

@cocotb.test()
async def test_alu_logical_or(dut):
    """ALU Test: Bitwise OR operation"""
    dut.A.value = 0x0F0F0F0F
    dut.B.value = 0x33333333
    dut.FS.value = FS_OR
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == (0x0F0F0F0F | 0x33333333)

@cocotb.test()
async def test_alu_shift_left(dut):
    """ALU Test: Shifter 1-bit Left Shift and Carry tracking"""
    dut.A.value = 0x8000000F  # MSB is 1
    dut.B.value = 0           # Shifter ignores B
    dut.FS.value = FS_SLL
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == 0x0000001E
    assert int(dut.C.value) == 1  # The original bit 31 dropped out into C

@cocotb.test()
async def test_alu_shift_right(dut):
    """ALU Test: Shifter 1-bit Right Shift and Carry tracking"""
    dut.A.value = 0xF0000001  # LSB is 1
    dut.B.value = 0
    dut.FS.value = FS_SRL
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == 0x78000000
    assert int(dut.C.value) == 1  # The original bit 0 dropped out into C
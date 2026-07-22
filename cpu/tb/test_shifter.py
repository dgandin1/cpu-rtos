import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_shifter_operations(dut):
    """Test 1-bit Left and Right shift operations with Carry tracking"""

    # --- Test Case 1: Shift Left (LR = 0) ---
    # Input has a 1 in the MSB (bit 31) and some other bits
    dut.A.value = 0x8000000F  # Binary: 1000...0000 1111
    dut.LR.value = 0          # Shift Left
    
    await Timer(1, unit="ns")
    
    # Expected Y: The lower bits move left by 1 (0x0000000F becomes 0x0000001E)
    # The MSB (1) drops out into the Carry flag.
    assert dut.Y.value.to_unsigned() == 0x0000001E, f"Expected 0x0000001E, got {hex(dut.Y.value.to_unsigned())}"
    assert int(dut.C.value) == 1, "Carry bit should match the dropped MSB (bit 31)"

    # --- Test Case 2: Shift Right (LR = 1) ---
    # Input has a 1 in the LSB (bit 0) and a leading pattern
    dut.A.value = 0xF0000001  # Binary: 1111 0000...0001
    dut.LR.value = 1          # Shift Right
    
    await Timer(1, unit="ns")
    
    # Expected Y: The top bits move right by 1 (0xF... becomes 0x7...)
    # The LSB (1) drops out into the Carry flag.
    assert dut.Y.value.to_unsigned() == 0x78000000, f"Expected 0x78000000, got {hex(dut.Y.value.to_unsigned())}"
    assert int(dut.C.value) == 1, "Carry bit should match the dropped LSB (bit 0)"

    # --- Test Case 3: Shift Right without dropping a '1' ---
    dut.A.value = 0xF0000002  # Binary ends in ...0010 (bit 0 is 0)
    dut.LR.value = 1
    
    await Timer(1, unit="ns")
    
    assert dut.Y.value.to_unsigned() == 0x78000001
    assert int(dut.C.value) == 0, "Carry bit should be 0 since bit 0 was 0"
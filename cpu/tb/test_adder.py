import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_simple(dut):

    a = 156456
    b = 2345346

    dut.A.value = a
    dut.B.value = b

    await Timer(1, unit="ns")

    assert dut.Y.value.to_unsigned() == a + b
    assert int(dut.C.value) == 0
    assert int(dut.V.value) == 0

@cocotb.test()
async def test_signed_overflow(dut):

    a = 2**31 - 1
    b = 5

    dut.A.value = a
    dut.B.value = b

    await Timer(1, unit="ns")

    assert dut.Y.value.to_unsigned() == a + b
    assert int(dut.C.value) == 0
    assert int(dut.V.value) == 1

@cocotb.test()
async def test_unsigned_overflow(dut):
    """Test Unsigned Overflow: Max unsigned int + 5 causes a carry-out"""

    a = 2**32 - 1  # Maximum 32-bit unsigned value (0xFFFFFFFF)
    b = 5

    dut.A.value = a
    dut.B.value = b

    await Timer(1, unit="ns")

    # 1. Y wraps around. 0xFFFFFFFF + 5 = 0x100000004. 
    # Truncated to 32 bits, this equals 4.
    assert dut.Y.value.to_unsigned() == ((a + b) & 0xFFFFFFFF)
    
    # 2. Unsigned carry DID occur because the result exceeded 32 bits.
    assert int(dut.C.value) == 1
    
    # 3. Signed overflow did NOT occur. 
    # In signed space, this was (-1) + (5) = 4, which is mathematically correct.
    assert int(dut.V.value) == 0
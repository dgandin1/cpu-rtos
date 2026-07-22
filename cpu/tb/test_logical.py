import cocotb
from cocotb.triggers import Timer

@cocotb.test()
async def test_logical_operations(dut):
    """Test both AND and OR operations in the logical unit"""

    a_val = 0x0F0F0F0F
    b_val = 0x33333333

    dut.A.value = a_val
    dut.B.value = b_val

    # 1. Test Bitwise AND (OA = 1)
    dut.OA.value = 1
    await Timer(1, unit="ns")
    assert dut.Y.value.to_unsigned() == (a_val & b_val)

    # 2. Test Bitwise OR (OA = 0)
    dut.OA.value = 0
    await Timer(1, unit="ns")
    assert dut.Y.value.to_unsigned() == (a_val | b_val)
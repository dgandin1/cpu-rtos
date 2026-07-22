import cocotb
from cocotb.triggers import Timer

# Define the localparam constants from the Verilog module
FS_ADD = 0b000
FS_SUB = 0b001
FS_SRL = 0b010
FS_SLL = 0b011
FS_AND = 0b100
FS_OR  = 0b110
FS_DEF = 0b101 # An unmapped value to test the default case

@cocotb.test()
async def test_controller_modes(dut):
    """Test all function selection configurations for the ALU controller"""

    # --- 1. Test ADD Mode ---
    dut.FS.value = FS_ADD
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b00
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b00

    # --- 2. Test SUB Mode ---
    dut.FS.value = FS_SUB
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 1
    assert int(dut.CISEL.value) == 1
    assert int(dut.OSEL.value) == 0b00
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b00

    # --- 3. Test SRL (Shift Right Logical) ---
    dut.FS.value = FS_SRL
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b01
    assert int(dut.SHIFT_LR.value) == 1
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b01

    # --- 4. Test SLL (Shift Left Logical) ---
    dut.FS.value = FS_SLL
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b01
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b01

    # --- 5. Test AND ---
    dut.FS.value = FS_AND
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b10
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 1
    assert int(dut.CSEL.value) == 0b10

    # --- 6. Test OR ---
    dut.FS.value = FS_OR
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b10
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b10

    # --- 7. Test Default Case ---
    dut.FS.value = FS_DEF
    await Timer(1, unit="ns")
    assert int(dut.BSEL.value) == 0
    assert int(dut.CISEL.value) == 0
    assert int(dut.OSEL.value) == 0b00
    assert int(dut.SHIFT_LR.value) == 0
    assert int(dut.LOGICAL_OA.value) == 0
    assert int(dut.CSEL.value) == 0b00
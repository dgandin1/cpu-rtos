import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ClockCycles

async def setup_clock(dut):
    """Helper to start the clock generator"""
    clock = Clock(dut.CLK, 10, unit="ns")  # 100 MHz clock
    cocotb.start_soon(clock.start())

@cocotb.test()
async def test_regfile_reset(dut):
    """Regfile Test: Verify asynchronous/synchronous reset behavior"""
    await setup_clock(dut)
    
    # Assert reset
    dut.RESET.value = 1
    dut.LD.value = 0
    dut.SA.value = 0
    dut.SB.value = 15
    
    await ClockCycles(dut.CLK, 2)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Check that registers within the reset range are 0
    assert dut.DataA.value.to_unsigned() == 0, "Register 0 failed to reset!"
    assert dut.DataB.value.to_unsigned() == 0, "Register 15 failed to reset!"

@cocotb.test()
async def test_regfile_write_and_read(dut):
    """Regfile Test: Write to a register and read it back from both ports"""
    await setup_clock(dut)
    
    # Clear reset state
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)
    
    # Write 0xDEADBEEF to Register 5
    dut.LD.value = 1
    dut.DR.value = 5
    dut.D_in.value = 0xDEADBEEF
    
    # Wait for one rising edge clock cycle to lock in the write
    await ClockCycles(dut.CLK, 1)
    
    # Turn off write enable so we don't overwrite data accidentally
    dut.LD.value = 0
    
    # Point Source A and Source B to Register 5
    dut.SA.value = 5
    dut.SB.value = 5
    await FallingEdge(dut.CLK) # Wait for combinational paths to settle
    
    assert dut.DataA.value.to_unsigned() == 0xDEADBEEF, "Port A read back wrong data!"
    assert dut.DataB.value.to_unsigned() == 0xDEADBEEF, "Port B read back wrong data!"

@cocotb.test()
async def test_regfile_no_write_without_enable(dut):
    """Regfile Test: Ensure no data is written when LD is low"""
    await setup_clock(dut)
    
    # Set up basic pointers
    dut.RESET.value = 0
    dut.SA.value = 10
    
    # Attempt a write with LD = 0
    dut.LD.value = 0
    dut.DR.value = 10
    dut.D_in.value = 0xAAAAAAA5
    
    await ClockCycles(dut.CLK, 1)
    await FallingEdge(dut.CLK)
    
    # The value should remain 0 (or whatever it was post-reset)
    assert dut.DataA.value.to_unsigned() == 0, "Data was written even though LD was disabled!"
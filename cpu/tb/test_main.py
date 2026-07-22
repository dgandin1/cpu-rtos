import cocotb
from cocotb.triggers import Timer, ClockCycles, FallingEdge
from cocotb.clock import Clock


@cocotb.test()
async def test_cpu_hex_file_execution(dut):
    """CPU Master Test: Run a custom compiled program.hex file"""
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())
    
    # 1. Initialize data values into registers before running
    dut.RESET.value = 1
    await ClockCycles(dut.CLK, 2)
    
    await Timer(1, unit="ns")

    # 2. Release reset to let the program.hex execution begin
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    dut._log.info("--- CPU Released from Reset: Executing program.hex ---")

    # 3. Let it run for enough clock cycles to finish your hex code payload
    # Increase this number if your hex file has more instructions!
    await ClockCycles(dut.CLK, 30000) 

    # 4. Dump the final state of all general-purpose registers
    dut._log.info("======================================")
    dut._log.info("       FINAL CPU REGISTER FILE        ")
    dut._log.info("======================================")
    
    for idx in range(32):
        # Dynamically pull value from your regfile internal 'storage' array
        try:
            reg_val = dut.register.storage[idx].value.to_unsigned()
            dut._log.info(f"  Register r{idx:02d} : {reg_val}")
        except AttributeError:
            # Handle situations where specific simulator backends optimize away unused indices
            pass
    await ClockCycles(dut.CLK, 1)
    dut._log.info("FINAL OUTPUT LCD:")
    dut.data_memory.ADDR.value = 0x00000001
    mem_val = dut.data_memory.DATA_OUT.value.to_unsigned()
    dut._log.info(mem_val)
            
    dut._log.info("======================================")
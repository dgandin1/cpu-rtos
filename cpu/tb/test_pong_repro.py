import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, ClockCycles, Timer

@cocotb.test()
async def test_reproduce_pong_reset(dut):
    """Simulate program.hex and monitor if PC ever resets to 0 after initial boot."""
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start())

    from pathlib import Path
    hex_path = Path(__file__).resolve().parent.parent / "rtl" / "program.hex"
    with open(hex_path) as f:
        lines = [line.strip() for line in f if line.strip()]

    for i, line in enumerate(lines):
        dut.instruction_memory.mem[i].value = int(line, 16)

    dut.RESET.value = 1
    dut.key_w.value = 0
    dut.key_s.value = 0
    await ClockCycles(dut.CLK, 5)
    await FallingEdge(dut.CLK)
    dut.RESET.value = 0
    await FallingEdge(dut.CLK)

    dut._log.info("Booted! Monitoring for resets to PC=0...")

    # Run for 20,000 cycles, occasionally pulsing key_w or key_s, or letting PIT fire
    for cycle in range(30000):
        await RisingEdge(dut.CLK)
        await FallingEdge(dut.CLK)

        pc = int(dut.PC_current.value)
        mepc = int(dut.MEPC.value)
        mie = int(dut.MIE.value)
        irq_pend = int(dut.irq_pending.value)

        # Pulse key_w occasionally
        if cycle in [150, 432, 1205, 3041, 5500, 8912, 15000]:
            dut._log.info(f"[Cycle {cycle}] Triggering key_w interrupt at PC={pc}")
            dut.key_w.value = 1
        elif cycle in [151, 433, 1206, 3042, 5501, 8913, 15001]:
            dut.key_w.value = 0

        # Pulse key_s occasionally
        if cycle in [300, 789, 2100, 4400, 7200, 11000]:
            dut._log.info(f"[Cycle {cycle}] Triggering key_s interrupt at PC={pc}")
            dut.key_s.value = 1
        elif cycle in [301, 790, 2101, 4401, 7201, 11001]:
            dut.key_s.value = 0

        if 1200 <= cycle <= 1260:
            dut._log.info(
                f"[Cycle {cycle}] PC={pc:3d} Iin=0x{int(dut.Iin.value):08x} "
                f"| IF/ID: pc={int(dut.if_id_pc.value):3d} instr=0x{int(dut.if_id_instr.value):08x} "
                f"| ID/EX: pc={int(dut.id_ex_pc.value):3d} br={int(dut.id_ex_is_branch.value)} mret={int(dut.id_ex_is_mret.value)} "
                f"| EX: take_irq={int(dut.take_interrupt.value)} redir={int(dut.ex_redirect.value)} "
                f"| MEPC={mepc:3d} MIE={mie} irq_pend={irq_pend}"
            )

        # Check if PC returned to 0 after booting (cycle > 50)
        if cycle > 50 and pc == 0:
            dut._log.error(f"BUG DETECTED at cycle {cycle}! PC reset to 0! MEPC={mepc}, MIE={mie}, irq_pending={irq_pend}")
            assert False, f"CPU reset to PC=0 at cycle {cycle}! MEPC was {mepc}"

import os
from pathlib import Path
from cocotb_tools.runner import get_runner

def run_pong():
    sim = os.getenv("SIM", "verilator")
    proj_dir = Path(__file__).resolve().parent.parent / "rtl"
    build_dir = proj_dir / "sim_build" / "pipe"
    build_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        proj_dir / "decoder.v",
        proj_dir / "controller.v",
        proj_dir / "adder.v",
        proj_dir / "logical.v",
        proj_dir / "shifter.v",
        proj_dir / "alu.v",
        proj_dir / "pc.v",
        proj_dir / "iram.v",
        proj_dir / "dram.v",
        proj_dir / "regfile.v",
        proj_dir / "pit.v",
        proj_dir / "vga_controller.v",
        proj_dir / "sram.v",
        proj_dir / "cache_controller.v",
        proj_dir / "mcu_disk.v",
        proj_dir / "cpu.v",
    ]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="cpu",
        build_dir=build_dir,
        waves=False,
        build_args=[
            "-Wall",
            "-Wno-fatal",
            "-O3",
            "-CFLAGS",
            "-O3 -march=native",
            "--x-assign",
            "fast",
            "--x-initial",
            "fast"
        ],
    )

    runner.test(
        hdl_toplevel="cpu",
        test_module="test_pong_repro",
        build_dir=build_dir,
        waves=False,
    )

if __name__ == "__main__":
    run_pong()

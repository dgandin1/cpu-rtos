import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
import pygame
import os
from pathlib import Path
from cocotb_tools.runner import get_runner

@cocotb.test()
async def run_debugger(dut):

    #cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start()) #100 Mhz
    dut.CLK.value = 0
    
    dut.RESET.value = 1

    dut.CLK.value = 0
    dut.CLK.value = 1
    dut.CLK.value = 0
    
    dut.RESET.value = 0

    dut.CLK.value = 1

    print("Simultion Started. Enter command: ")

    while True:
        command = input(">")

        if command == "step":
            dut.CLK.value = 0
            dut.CLK.value = 1
            print(" RAN: ")
        if command.startswith("reg"):
            reg = int(command.split()[1])
            print("Register R1: ")

    


if __name__ == "__main__":


    sim = os.getenv("SIM", "verilator")
    proj_dir = Path(__file__).resolve().parent.parent / "rtl"
    build_dir = proj_dir / "sim_build"
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
            proj_dir / "cpu.v",
            proj_dir / "pit.v"
        ]

    runner = get_runner(sim)
    runner.build(
            sources=sources,
            hdl_toplevel="cpu",               
            build_dir=proj_dir / "sim_build",  
            waves=True,                        
            build_args=["--trace", "-Wall"]   
        )

    runner.test(
            hdl_toplevel="cpu",
            test_module="run_sim",            
            testcase="run_debugger", 
            waves=True
        )

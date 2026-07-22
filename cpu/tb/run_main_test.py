import os
from pathlib import Path
from cocotb_tools.runner import get_runner

def test_cpu_runner():

    # Force create/ensure program.hex is inside the execution directory
    
    """Top-level simulation runner using Verilator"""
    
    # Establish base paths
    hdl_toplevel_lang = os.getenv("HDL_TOPLEVEL_LANG", "verilog")
    sim = os.getenv("SIM", "verilator")
    
    proj_dir1 = Path(__file__).resolve().parent.parent
    proj_dir = proj_dir1 / "rtl"

    # NEW CODE: This creates the hex file right in the active execution directory
    # so Verilator is guaranteed to find it!
    hex_payload = "00108093\n00108093\n00108093\n00108093\n"
    build_dir = proj_dir / "sim_build"
    build_dir.mkdir(parents=True, exist_ok=True) # Ensure the folder exists first
    # Write it to the current directory (tb/)

    
    # 1. Define all your source Verilog files in compilation order
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
        proj_dir / "cpu.v"  # Make sure the top-level module is included
    ]
    
    # 2. Get the Verilator simulation object
    runner = get_runner(sim)
    
    # 3. Configure and compile the simulation binary
    # Configure and compile the simulation binary
    runner.build(
        sources=sources,
        hdl_toplevel="cpu",               
        build_dir=proj_dir / "sim_build",  
        waves=True,                        
        build_args=["--trace", "-Wall"]    # <-- Changed extra_args to build_args
    )
    # 4. Execute the simulation
    runner.test(
        hdl_toplevel="cpu",
        test_module="test_main",            # Name of your test_cpu.py file (without .py)
        testcase="test_cpu_hex_file_execution", # Explicitly run your hex testcase
        waves=True
    )

if __name__ == "__main__":
    test_cpu_runner()
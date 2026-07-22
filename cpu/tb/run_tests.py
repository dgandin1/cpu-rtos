# tests/run_tests.py
import os
from pathlib import Path
from cocotb_tools.runner import get_runner

def run_cocotb_test(module_name: str):
    """Helper function to compile and run a single hardware module test."""
    sim = os.getenv("SIM", "verilator")
    proj_path = Path(__file__).resolve().parent.parent
    
    runner = get_runner(sim)
    
    # Define which files are needed for compilation
    rtl_dir = proj_path / "rtl"
    if module_name == "alu":
        # The ALU needs ALL sub-modules compiled along with it
        src_files = [
            rtl_dir / "controller.v",
            rtl_dir / "adder.v",
            rtl_dir / "logical.v",
            rtl_dir / "shifter.v",
            rtl_dir / "alu.v"
        ]
    elif module_name == "cpu":
        src_files = [
            rtl_dir / "regfile.v",
            rtl_dir / "cpu.v",
            rtl_dir / "decoder.v",
            rtl_dir / "alu.v",
            rtl_dir / "controller.v",
            rtl_dir / "adder.v",
            rtl_dir / "logical.v",
            rtl_dir / "shifter.v",
            rtl_dir / "iram.v",
            rtl_dir / "pc.v",
            rtl_dir / "dram.v"
        ]
    else:
        # Standalone component tests only need their own file
        src_files = [rtl_dir / f"{module_name}.v"]
    
    # Fix: Use 'sources' parameter instead of deprecated 'verilog_sources'
    runner.build(
        sources=src_files,
        hdl_toplevel=module_name,
        always=True,
    )
    
    runner.test(
        hdl_toplevel=module_name, 
        test_module=f"test_{module_name}"
    )

if __name__ == "__main__":
    modules_to_test = [
        "cpu",
        "regfile",
        "alu",  # Put alu last so the individual units pass first!
        "decoder",
        "adder",
        "controller",
        "logical",
    ]
    
    for module in modules_to_test:
        print(f"\n--- Running Verification for: {module} ---")
        run_cocotb_test(module)
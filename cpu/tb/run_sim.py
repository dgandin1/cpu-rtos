import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock
import pygame
import os
from pathlib import Path
from cocotb_tools.runner import get_runner

SCREEN_WIDTH = 64
SCREEN_HEIGHT = 64
PIXEL_SCALE = 8 # Scale up screen on pygame side so it is easier to see
BUFFER_BASE_ADDR = 101

async def display_driver(dut):

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH * PIXEL_SCALE, SCREEN_HEIGHT * PIXEL_SCALE))
    pygame.display.set_caption("CPU Output Framebuffer")

    while True:

        await Timer(100, unit="us")

        # Get if there are any print results
        mem = dut.data_memory.mem[1].value.to_unsigned()
        if not mem == 0:
            print(mem)
            dut.data_memory.mem[1].value = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    dut.IRQ_in.value = 1  # or 1000 if it's a wide bus
                    await Timer(10, unit="ns")
                    dut.IRQ_in.value = 0

        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                # 1. Calculate which word holds pixel (x, y)
                word_x = x // 32
                words_per_row = SCREEN_WIDTH // 32 # 64 // 32 = 2
                addr = BUFFER_BASE_ADDR + (y * words_per_row) + word_x

                # 2. Extract the specific bit (x % 32)
                bit_index = x % 32
                word_val = int(dut.data_memory.mem[addr].value)
                pixel_is_on = (word_val >> bit_index) & 1

                # 3. Choose color based on bit state
                color = (255, 255, 255) if pixel_is_on else (0, 0, 0)

                rect = (x * PIXEL_SCALE, y * PIXEL_SCALE, PIXEL_SCALE, PIXEL_SCALE)
                pygame.draw.rect(screen, color, rect)

        pygame.display.flip()

@cocotb.test()
async def run_cpu_with_screen(dut):
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start()) #100 Mhz

    dut.RESET.value = 1
    await Timer(50, unit="ns")
    dut.RESET.value = 0

    cocotb.start_soon(display_driver(dut))

    while True:
        await Timer(1, unit="ms")



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
            proj_dir / "cpu.v"  
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
            testcase="run_cpu_with_screen", 
            waves=True
        )



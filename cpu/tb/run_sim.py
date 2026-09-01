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

    # 1. Create native 64x64 offscreen buffer
    buffer_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

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
                if event.key == pygame.K_w:
                    dut.key_w.value = 1
                    await Timer(10, unit="ns")
                    dut.key_w.value = 0
                if event.key == pygame.K_s:
                    dut.key_s.value = 1
                    await Timer(10, unit="ns")
                    dut.key_s.value = 0

        # 2. Attach PixelArray to offscreen buffer_surface instead of screen
        px_array = pygame.PixelArray(buffer_surface)
        words_per_row = SCREEN_WIDTH // 32

        for y in range(SCREEN_HEIGHT):
            row_addr = BUFFER_BASE_ADDR + (y * words_per_row)
            w0 = int(dut.data_memory.mem[row_addr].value)
            w1 = int(dut.data_memory.mem[row_addr + 1].value)

            for x in range(32):
                px_array[x, y] = (255, 255, 255) if ((w0 >> x) & 1) else (0, 0, 0)
                px_array[x + 32, y] = (255, 255, 255) if ((w1 >> x) & 1) else (0, 0, 0)

        del px_array  # Unlock surface

        # 3. Scale native 64x64 surface to match full display resolution
        scaled = pygame.transform.scale(buffer_surface, (SCREEN_WIDTH * PIXEL_SCALE, SCREEN_HEIGHT * PIXEL_SCALE))
        screen.blit(scaled, (0, 0))

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
            proj_dir / "cpu.v",
            proj_dir / "pit.v"
        ]

    runner = get_runner(sim)
    runner.build(
            sources=sources,
            hdl_toplevel="cpu",               
            build_dir=proj_dir / "sim_build",  
            waves=False,                        
            build_args=["-Wall", "-O3", "-CFLAGS", "-O3 -march=native", "--x-assign", "fast", "--x-initial", "fast"]   
        )

    runner.test(
            hdl_toplevel="cpu",
            test_module="run_sim",            
            testcase="run_cpu_with_screen", 
            waves=False
        )



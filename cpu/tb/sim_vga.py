import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import pygame
import os
from pathlib import Path
from cocotb_tools.runner import get_runner

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

shutdown_flag = False

async def cpu_io_handler(dut):
    """Handles keyboard input, OS quit events, and CPU print() statements."""
    global shutdown_flag
    
    while True:
        await Timer(100, unit="us")

        # Poll memory address 1 for print() results
        try:
            mem = dut.data_memory.mem[1].value.integer
            if mem != 0:
                print(f"CPU Print: {mem}")
                dut.data_memory.mem[1].value = 0
        except ValueError:
            pass # Ignore uninitialized memory at startup

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                shutdown_flag = True
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

async def vga_physical_monitor(dut, screen, buffer_surface):
    """Acts exactly like a hardware VGA monitor, reading pins at 25 MHz."""
    px_array = pygame.PixelArray(buffer_surface)
    x = 0
    y = 0
    
    # Wait for reset to finish before sampling pins
    await Timer(100, unit="ns")

    while True:
        # Sample exactly at the 25 MHz pixel clock rate
        await Timer(40, unit="ns")

        try:
            hsync = int(dut.hsync.value)
            vsync = int(dut.vsync.value)
            rgb = int(dut.rgb.value)
        except ValueError:
            continue # Skip if pins are in 'x' or 'z' uninitialized states

        # VGA State Machine Decoder
        if vsync == 0:
            y = -35  # V_SYNC (2) + V_BP (33)
        elif hsync == 0:
            x = -144 # H_SYNC (96) + H_BP (48)
            y += 1
        else:
            x += 1

        # If the electron beam is in the visible screen area
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            color = (255, 255, 255) if rgb else (0, 0, 0)
            px_array[x, y] = color

        # End of frame: update Pygame display
        if x == SCREEN_WIDTH - 1 and y == SCREEN_HEIGHT - 1:
            del px_array  # Unlock surface to blit
            screen.blit(buffer_surface, (0, 0))
            pygame.display.flip()
            px_array = pygame.PixelArray(buffer_surface)


@cocotb.test()
async def run_cpu_with_screen(dut):
    global shutdown_flag
    
    # Start the 100 MHz system clock
    cocotb.start_soon(Clock(dut.CLK, 10, unit="ns").start()) 

    # Initialize inputs
    dut.key_w.value = 0
    dut.key_s.value = 0
    dut.RESET.value = 1
    await Timer(50, unit="ns")
    dut.RESET.value = 0

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Physical VGA Hardware Monitor")
    buffer_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Launch parallel hardware drivers
    cocotb.start_soon(cpu_io_handler(dut))
    cocotb.start_soon(vga_physical_monitor(dut, screen, buffer_surface))

    # Keep simulation alive until Pygame window is closed
    while not shutdown_flag:
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
            proj_dir / "pit.v",
            proj_dir / "vga_controller.v", # Make sure this matches your new filename!
            proj_dir / "cpu.v"
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
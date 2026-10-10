# build.tcl
set project_name "cmod_s7_vga"
set output_dir "./vivado_build"

# 1. Create a new project for the Cmod S7 chip
create_project -force $project_name $output_dir -part xc7s25csga225-1

# 2. Add all your Verilog source files
add_files [glob ./rtl/*.v]

# 3. Add your physical constraints file
add_files -fileset constrs_1 ./constraints.xdc

# 4. Set the top-level module to your new wrapper
set_property top cmod_top [current_fileset]
update_compile_order -fileset sources_1

# 5. Generate the Clocking Wizard IP (12 MHz to 100 MHz)
create_ip -name clk_wiz -vendor xilinx.com -library ip -module_name clk_wiz_0
set_property -dict [list \
    CONFIG.PRIM_IN_FREQ {12.000} \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {100.000} \
    CONFIG.USE_RESET {false} \
] [get_ips clk_wiz_0]
generate_target all [get_ips clk_wiz_0]

# 6. Run Synthesis
puts "Starting Synthesis..."
launch_runs synth_1 -jobs 4
wait_on_run synth_1

# 7. Run Implementation & Bitstream Generation
puts "Starting Implementation..."
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# 8. Copy the final bitstream out to the main directory for easy access
file copy -force $output_dir/${project_name}.runs/impl_1/cmod_top.bit ./cpu.bit
puts "Build complete! Bitstream saved as cpu.bit"
# rebuild.tcl
# Fast rebuild script that reuses pre-synthesized IP (clk_wiz_0, ila_0)
# and runs top-level synthesis + implementation + bitstream generation.

open_project ./vivado_build/cmod_s7_vga.xpr

# Ensure clk_wiz_0 is configured to 100 MHz
set clk_wiz [get_ips clk_wiz_0]
if {$clk_wiz ne ""} {
    set cur_freq [get_property CONFIG.CLKOUT1_REQUESTED_OUT_FREQ $clk_wiz]
    if {$cur_freq != "100.000"} {
        puts ">>> Updating clk_wiz_0 to 100 MHz..."
        set_property CONFIG.CLKOUT1_REQUESTED_OUT_FREQ 100.000 $clk_wiz
        generate_target all $clk_wiz
        reset_run clk_wiz_0_synth_1
        launch_runs clk_wiz_0_synth_1 -jobs 4
        wait_on_run clk_wiz_0_synth_1
    }
}

# Ensure all Verilog files in rtl/ (including cache_controller.v and sram.v) are added
add_files -norecurse [glob -nocomplain ./rtl/*.v]
update_compile_order -fileset sources_1

# Use Performance strategy with post-route physical optimization for 100 MHz timing margin
catch {set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]}

# Reset top-level synthesis run
reset_run synth_1

puts ">>> Launching Synthesis and Implementation to Bitstream @ 100 MHz..."
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

# Check if implementation succeeded
if {[get_property STATUS [get_runs impl_1]] == "write_bitstream Complete!"} {
    file copy -force ./vivado_build/cmod_s7_vga.runs/impl_1/cmod_top.bit ./cpu.bit
    open_run impl_1
    write_debug_probes -force cmod_top.ltx
    report_timing_summary -file ./vivado_build/timing_summary.rpt
    report_utilization -file ./vivado_build/cmod_top_utilization_placed.rpt

    set wns [get_property SLACK [get_timing_paths -max_paths 1 -setup]]
    set whs [get_property SLACK [get_timing_paths -max_paths 1 -hold]]
    set period 10.0
    set min_period [expr {$period - $wns}]
    set fmax [expr {1000.0 / $min_period}]

    puts "=========================================================="
    puts ">>> Fast build complete! Bitstream saved as cpu.bit <<<"
    puts [format ">>> Timing @ 100 MHz: WNS = %.3f ns | WHS = %.3f ns | Min Period = %.3f ns | Estimated Fmax = %.2f MHz <<<" $wns $whs $min_period $fmax]
    puts "=========================================================="
} else {
    puts "=========================================================="
    puts ">>> Build failed! Check impl_1 run log for details. <<<"
    puts "=========================================================="
}

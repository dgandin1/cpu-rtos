# 12 MHz System Clock (Cmod A7)
set_property -dict { PACKAGE_PIN L17 IOSTANDARD LVCMOS33 } [get_ports { clk_12mhz }];

# Buttons (Cmod A7)
set_property -dict { PACKAGE_PIN A18 IOSTANDARD LVCMOS33 } [get_ports { btn[0] }];
set_property -dict { PACKAGE_PIN B18 IOSTANDARD LVCMOS33 } [get_ports { btn[1] }];

# VGA Pins (Mapped to Cmod A7 Breadboard GPIO Pins 1-5)
set_property -dict { PACKAGE_PIN M3 IOSTANDARD LVCMOS33 } [get_ports { rgb[0] }];   # DIP Pin 1
set_property -dict { PACKAGE_PIN L3 IOSTANDARD LVCMOS33 } [get_ports { rgb[1] }];   # DIP Pin 2
set_property -dict { PACKAGE_PIN A16 IOSTANDARD LVCMOS33 } [get_ports { rgb[2] }]; # DIP Pin 3 (Red)
set_property -dict { PACKAGE_PIN K3 IOSTANDARD LVCMOS33 } [get_ports { hsync }];  # DIP Pin 4 (Green)
set_property -dict { PACKAGE_PIN C15 IOSTANDARD LVCMOS33 } [get_ports { vsync }]; # DIP Pin 5 (Blue)
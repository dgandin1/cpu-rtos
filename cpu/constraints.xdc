# 12 MHz System Clock (Cmod A7)
set_property -dict { PACKAGE_PIN L17 IOSTANDARD LVCMOS33 } [get_ports { clk_12mhz }];

# Buttons (Cmod A7)
set_property -dict { PACKAGE_PIN A18 IOSTANDARD LVCMOS33 } [get_ports { btn[0] }];
set_property -dict { PACKAGE_PIN B18 IOSTANDARD LVCMOS33 } [get_ports { btn[1] }];

# VGA Pins (Mapped to Cmod A7 Breadboard GPIO Pins 1-5)
set_property -dict { PACKAGE_PIN M3  IOSTANDARD LVCMOS33 } [get_ports { rgb[0] }];  # DIP Pin 1
set_property -dict { PACKAGE_PIN L3  IOSTANDARD LVCMOS33 } [get_ports { rgb[1] }];  # DIP Pin 2
set_property -dict { PACKAGE_PIN A16 IOSTANDARD LVCMOS33 } [get_ports { rgb[2] }];  # DIP Pin 3 (Red)
set_property -dict { PACKAGE_PIN K3  IOSTANDARD LVCMOS33 } [get_ports { hsync }];   # DIP Pin 4 (Green)
set_property -dict { PACKAGE_PIN C15 IOSTANDARD LVCMOS33 } [get_ports { vsync }];   # DIP Pin 5 (Blue)

# Microcontroller Disk UART (Cmod A7 DIP Pins 6 and 7)
set_property -dict { PACKAGE_PIN H1  IOSTANDARD LVCMOS33 PULLUP true } [get_ports { mcu_rx }]; # DIP Pin 6
set_property -dict { PACKAGE_PIN A15 IOSTANDARD LVCMOS33 }             [get_ports { mcu_tx }]; # DIP Pin 7

# External 512KB Static RAM (ISSI IS61WV5128BLL-10BLI) Control Signals
set_property -dict { PACKAGE_PIN N19 IOSTANDARD LVCMOS33 } [get_ports { RamCEn }]; # Sch=sram-ce
set_property -dict { PACKAGE_PIN P19 IOSTANDARD LVCMOS33 } [get_ports { RamOEn }]; # Sch=sram-oe
set_property -dict { PACKAGE_PIN R19 IOSTANDARD LVCMOS33 } [get_ports { RamWEn }]; # Sch=sram-we

# External 512KB Static RAM Address Bus (MemAdr[18:0])
set_property -dict { PACKAGE_PIN N18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[0] }];  # Sch=sram-a[0]
set_property -dict { PACKAGE_PIN M19 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[1] }];  # Sch=sram-a[1]
set_property -dict { PACKAGE_PIN K17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[2] }];  # Sch=sram-a[2]
set_property -dict { PACKAGE_PIN N17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[3] }];  # Sch=sram-a[3]
set_property -dict { PACKAGE_PIN P17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[4] }];  # Sch=sram-a[4]
set_property -dict { PACKAGE_PIN P18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[5] }];  # Sch=sram-a[5]
set_property -dict { PACKAGE_PIN R18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[6] }];  # Sch=sram-a[6]
set_property -dict { PACKAGE_PIN W19 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[7] }];  # Sch=sram-a[7]
set_property -dict { PACKAGE_PIN U19 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[8] }];  # Sch=sram-a[8]
set_property -dict { PACKAGE_PIN V19 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[9] }];  # Sch=sram-a[9]
set_property -dict { PACKAGE_PIN W18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[10] }]; # Sch=sram-a[10]
set_property -dict { PACKAGE_PIN T17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[11] }]; # Sch=sram-a[11]
set_property -dict { PACKAGE_PIN T18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[12] }]; # Sch=sram-a[12]
set_property -dict { PACKAGE_PIN U17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[13] }]; # Sch=sram-a[13]
set_property -dict { PACKAGE_PIN U18 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[14] }]; # Sch=sram-a[14]
set_property -dict { PACKAGE_PIN V16 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[15] }]; # Sch=sram-a[15]
set_property -dict { PACKAGE_PIN W16 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[16] }]; # Sch=sram-a[16]
set_property -dict { PACKAGE_PIN W17 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[17] }]; # Sch=sram-a[17]
set_property -dict { PACKAGE_PIN V15 IOSTANDARD LVCMOS33 } [get_ports { MemAdr[18] }]; # Sch=sram-a[18]

# External 512KB Static RAM Bidirectional Data Bus (MemDB[7:0])
set_property -dict { PACKAGE_PIN W15 IOSTANDARD LVCMOS33 } [get_ports { MemDB[0] }];  # Sch=sram-dq[0]
set_property -dict { PACKAGE_PIN W13 IOSTANDARD LVCMOS33 } [get_ports { MemDB[1] }];  # Sch=sram-dq[1]
set_property -dict { PACKAGE_PIN W14 IOSTANDARD LVCMOS33 } [get_ports { MemDB[2] }];  # Sch=sram-dq[2]
set_property -dict { PACKAGE_PIN U15 IOSTANDARD LVCMOS33 } [get_ports { MemDB[3] }];  # Sch=sram-dq[3]
set_property -dict { PACKAGE_PIN U16 IOSTANDARD LVCMOS33 } [get_ports { MemDB[4] }];  # Sch=sram-dq[4]
set_property -dict { PACKAGE_PIN V13 IOSTANDARD LVCMOS33 } [get_ports { MemDB[5] }];  # Sch=sram-dq[5]
set_property -dict { PACKAGE_PIN V14 IOSTANDARD LVCMOS33 } [get_ports { MemDB[6] }];  # Sch=sram-dq[6]
set_property -dict { PACKAGE_PIN U14 IOSTANDARD LVCMOS33 } [get_ports { MemDB[7] }];  # Sch=sram-dq[7]

TOPLEVEL_LANG = verilog

VERILOG_SOURCES = $(shell find rtl -name "*.v")

TOPLEVEL = cpu
MODULE = test_cpu

SIM = verilator
export LD_LIBRARY_PATH=/home/duke/dev/cpu-rtos/cpu/Python-3.12.13:$LD_LIBRARY_PATH
include $(shell cocotb-config --makefiles)/Makefile.sim

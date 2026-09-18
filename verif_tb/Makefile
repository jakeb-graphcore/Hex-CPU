VERILOG_SOURCES += $(abspath testbench.sv)
VERILOG_SOURCES += $(abspath arch_monitor.sv)
VERILOG_SOURCES += $(abspath ../designs/$(DESIGN).sv)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOPLEVEL = testbench
MODULE = main

COMPILE_ARGS += -g2012

# export COCOTB_PDB_ON_EXCEPTION := 0

include $(shell cocotb-config --makefiles)/Makefile.sim

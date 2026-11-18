SIM ?= verilator
TOPLEVEL_LANG ?= verilog

RTL := $(CURDIR)/../../hdl_design/hdl_design.srcs/rtl

VERILOG_SOURCES += $(RTL)/registers/sync_nstage.sv
VERILOG_SOURCES += $(RTL)/posedge_detector.sv
VERILOG_SOURCES += $(RTL)/registers/spi.sv
VERILOG_SOURCES += $(RTL)/registers/dac/dac_regs_mod_pkg.sv
VERILOG_SOURCES += $(RTL)/registers/dac/dac_regs_mod.sv
VERILOG_SOURCES += $(RTL)/dac_datapath.sv
VERILOG_SOURCES += $(RTL)/test_dac_top.sv

# PeakRDL regblock trips MULTIDRIVEN; unused cpuif ack/stall pins trip PINMISSING.
COMPILE_ARGS += --trace --trace-structs -Wno-MULTIDRIVEN -Wno-PINMISSING
SIM_ARGS     += --trace

%.sim:
	$(MAKE) sim TOPLEVEL=$* COCOTB_TEST_MODULES=tb_$* 2>&1 | tee verilator.log

%.wave:
	gtkwave dump.vcd

include $(shell cocotb-config --makefiles)/Makefile.sim

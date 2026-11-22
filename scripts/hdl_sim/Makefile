SIM ?= verilator
TOPLEVEL_LANG ?= verilog

RTL := $(CURDIR)/../../hdl_design/hdl_design.srcs/rtl

VERILOG_SOURCES += $(RTL)/registers/sync_nstage.sv
VERILOG_SOURCES += $(RTL)/posedge_detector.sv
VERILOG_SOURCES += $(RTL)/registers/spi.sv
VERILOG_SOURCES += $(RTL)/registers/dac/dac_regs_mod_pkg.sv
VERILOG_SOURCES += $(RTL)/registers/dac/dac_regs_mod.sv
VERILOG_SOURCES += $(RTL)/dac_datapath.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/phase_accumulator.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/cordic_glue_logic.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/cordic.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/cordic_rom.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/bypass_mux.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/dsm_error_feedback.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/dac5311_shift_reg.sv
VERILOG_SOURCES += $(RTL)/dac_datapath_submodules/dac5311_ctrl.sv
VERILOG_SOURCES += $(RTL)/test_dac_top.sv

# PeakRDL regblock trips MULTIDRIVEN; unused cpuif ack/stall pins trip PINMISSING.
COMPILE_ARGS += --trace --trace-structs -Wno-MULTIDRIVEN -Wno-PINMISSING
SIM_ARGS     += --trace

%.sim:
	$(MAKE) sim TOPLEVEL=$* COCOTB_TEST_MODULES=tests.test_$* 2>&1 | tee verilator.log

%.wave:
	gtkwave dump.vcd

# If cocotb-config is missing, the include path collapses to /Makefile.sim and
# would otherwise match %.sim forever. Fail clearly instead.
/Makefile.sim:
	$(error cocotb-config not found; activate the venv or put cocotb on PATH)

include $(shell cocotb-config --makefiles)/Makefile.sim

# Extend cocotb's clean:: (root `make clean` recurses here).
clean::
	@$(RM) -f verilator.log

# make hdltest.dac_top -> MODULE=test_dac_top, Verilog top test_dac_top.
#
# test_dac_top is the DAC subsystem (host SPI and DAC5311 pins).
# The cocotb test drives those flat pins. hwif structs are not poked.

HDL_RTL := $(REPO_ROOT)/hdl_design/hdl_design.srcs/rtl
DAC_REGS_DIR := $(HDL_RTL)/registers/dac
DAC_PKG := $(DAC_REGS_DIR)/dac_regs_mod_pkg.sv
DAC_MOD := $(DAC_REGS_DIR)/dac_regs_mod.sv

VERILOG_SOURCES += \
	$(DAC_PKG) \
	$(DAC_MOD) \
	$(HDL_RTL)/registers/spi.sv \
	$(HDL_RTL)/registers/sync_nstage.sv \
	$(HDL_RTL)/posedge_detector.sv \
	$(HDL_RTL)/dac_datapath/phase_accumulator.sv \
	$(HDL_RTL)/dac_datapath/cordic.sv \
	$(HDL_RTL)/dac_datapath/dsm_error_feedback.sv \
	$(HDL_RTL)/dac_datapath/dsm_bypass_mux.sv \
	$(HDL_RTL)/dac_datapath/dac5311_ctrl.sv \
	$(HDL_RTL)/dac_datapath.sv \
	$(HDL_RTL)/test_dac_top.sv

COCOTB_TOPLEVEL := test_dac_top

# Generated regblock structs, spi.sv, and posedge_detector.sv warn under
# Verilator. Those warnings are outside this skeleton. COMPILE_ARGS is
# the verilator invocation only, not the simulation command line.
COMPILE_ARGS += -Wno-fatal

# Generate before cocotb's simulator makefile chooses its default goal.
# A real rule here would become that goal and skip the test.
$(shell mkdir -p $(DAC_REGS_DIR) && python3 $(REPO_ROOT)/scripts/hdl_sim/gen_dac_hwif.py $(DAC_REGS_DIR))
ifeq ($(wildcard $(DAC_PKG)),)
$(error dac_regs_mod_pkg.sv was not generated. peakrdl-regblock is required, same as scripts/registers.py)
endif

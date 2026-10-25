# make hdltest.dac_datapath -> MODULE=test_dac_datapath
#
# dac_regs_mod_pkg is generated (gitignored) from dac_registers.rdl.
# The block test elaborates dac_datapath, not test_dac_top: that
# wrapper also pulls in spi.sv, which this scaffold does not fix.

HDL_RTL := $(REPO_ROOT)/hdl_design/hdl_design.srcs/rtl
DAC_REGS_DIR := $(HDL_RTL)/registers/dac
DAC_PKG := $(DAC_REGS_DIR)/dac_regs_mod_pkg.sv

VERILOG_SOURCES += \
	$(DAC_PKG) \
	$(HDL_RTL)/dac_datapath/phase_accumulator.sv \
	$(HDL_RTL)/dac_datapath/cordic.sv \
	$(HDL_RTL)/dac_datapath/dsm_error_feedback.sv \
	$(HDL_RTL)/dac_datapath/dac5311_ctrl.sv \
	$(HDL_RTL)/dac_datapath.sv

COCOTB_TOPLEVEL := dac_datapath

# Generate before cocotb's simulator makefile chooses its default goal.
# A real rule here would become that goal and skip the test.
$(shell mkdir -p $(DAC_REGS_DIR) && python3 $(REPO_ROOT)/scripts/hdl_sim/gen_dac_hwif.py $(DAC_REGS_DIR))
ifeq ($(wildcard $(DAC_PKG)),)
$(error dac_regs_mod_pkg.sv was not generated. peakrdl-regblock is required, same as scripts/registers.py)
endif

# make hdltest.dac_top  ->  MODULE=test_dac_top, Verilog top dac_top.
#
# test_dac_top.sv instantiates this skeleton, and also the generated
# dac_regs_mod, which is not checked in. The block test elaborates
# dac_top alone.

HDL_RTL := $(REPO_ROOT)/hdl_design/hdl_design.srcs/rtl

VERILOG_SOURCES += $(HDL_RTL)/dac_top.sv
COCOTB_TOPLEVEL := dac_top

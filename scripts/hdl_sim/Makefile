SIM ?= verilator
TOPLEVEL_LANG ?= verilog

EXTRA_ARGS += -f filelist.f

hdltest.%:
	$(MAKE) sim TOPLEVEL=$* COCOTB_TEST_MODULES=test_$*

include $(shell cocotb-config --makefiles)/Makefile.sim
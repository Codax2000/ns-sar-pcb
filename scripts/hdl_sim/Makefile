SIM ?= verilator
TOPLEVEL_LANG ?= verilog

EXTRA_ARGS   += -f filelist.f
COMPILE_ARGS += --trace --trace-structs
SIM_ARGS     += --trace

%.sim:
	$(MAKE) sim TOPLEVEL=$* COCOTB_TEST_MODULES=test_$*

%.wave:
	gtkwave sim_build/dump.fst

include $(shell cocotb-config --makefiles)/Makefile.sim
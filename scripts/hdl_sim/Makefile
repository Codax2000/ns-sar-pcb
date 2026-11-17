# Cocotb 2 + Verilator block tests.
#
# From the repository root (paths below are explained in README.md):
#   make hdltest TOPLEVEL=<hdl module> TEST=<python module> SOURCES=<file.f>
#   make hdltest TOPLEVEL=<hdl module> TEST=<python module> VERILOG_SOURCES="a.sv b.sv"
#   make hdltest.spi SOURCES=<file.f>
#
# TEST is the Python module (no .py) and becomes COCOTB_TEST_MODULES.
# TOPLEVEL is the HDL toplevel and becomes COCOTB_TOPLEVEL.
# SOURCES is a plain filelist passed to Verilator as -f.
# VERILOG_SOURCES is cocotb's source list, and can replace or supplement SOURCES.
#
# make / make help / make clean do not invoke Verilator. The simulator
# makefile is included only for the hdltest goal.

REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)

ifeq ($(OS),Windows_NT)
VENV_BIN := $(REPO_ROOT)/.venv/Scripts
ifneq ($(findstring sh,$(SHELL)),)
PATH_SEP := :
else
PATH_SEP := ;
endif
else
VENV_BIN := $(REPO_ROOT)/.venv/bin
PATH_SEP := :
endif

# cocotb's makefile runs cocotb-config via $(shell), which does not see a
# PATH export made in this same process. Restart once with .venv already
# on PATH. Command-line variables travel through MAKEFLAGS.
ifndef HDL_SIM_REEXEC
export PATH := $(VENV_BIN)$(PATH_SEP)$(PATH)

.PHONY: _hdl_sim_reexec
.DEFAULT_GOAL := _hdl_sim_reexec
_hdl_sim_reexec:
	@$(MAKE) --no-print-directory HDL_SIM_REEXEC=1 $(MAKECMDGOALS)

ifneq ($(MAKECMDGOALS),)
.PHONY: $(MAKECMDGOALS)
$(MAKECMDGOALS): _hdl_sim_reexec
	@:
endif

else

SIM ?= verilator
TOPLEVEL_LANG ?= verilog

.PHONY: help clean hdltest hdltest.spi
.DEFAULT_GOAL := help

help:
	@echo "make hdltest TOPLEVEL=<module> TEST=<python module> SOURCES=<file.f>"
	@echo "    or VERILOG_SOURCES=\"a.sv b.sv\" instead of (or in addition to) SOURCES"
	@echo "make hdltest.spi SOURCES=<file.f>"
	@echo "    TOPLEVEL=test_dac_top TEST=test_spi"
	@echo "make clean"

# Shortcut for the SPI register test. SOURCES / VERILOG_SOURCES stay
# whatever the command line already set.
hdltest.spi:
	@$(MAKE) --no-print-directory HDL_SIM_REEXEC=1 hdltest TOPLEVEL=test_dac_top TEST=test_spi

ifneq ($(filter hdltest,$(MAKECMDGOALS)),)

ifeq ($(strip $(TOPLEVEL)),)
$(error hdltest requires TOPLEVEL=<HDL toplevel module>)
endif

ifeq ($(strip $(TEST)),)
$(error hdltest requires TEST=<Python module name, without .py>)
endif

ifeq ($(strip $(SOURCES))$(strip $(VERILOG_SOURCES)),)
$(error hdltest requires SOURCES=<path to a .f filelist> or VERILOG_SOURCES=<SystemVerilog files>)
endif

ifneq ($(strip $(SOURCES)),)
# Command-line SOURCES cannot be reassigned. Accept a path relative to
# this directory or to the repository root (make -C lands here).
SOURCES_FILE := $(wildcard $(SOURCES))
ifeq ($(strip $(SOURCES_FILE)),)
SOURCES_FILE := $(wildcard $(REPO_ROOT)/$(SOURCES))
endif
ifeq ($(strip $(SOURCES_FILE)),)
$(error SOURCES file not found: $(SOURCES))
endif
COMPILE_ARGS += -f $(abspath $(SOURCES_FILE))
CUSTOM_COMPILE_DEPS += $(abspath $(SOURCES_FILE))
endif

COCOTB_TOPLEVEL := $(TOPLEVEL)
COCOTB_TEST_MODULES := $(TEST)
MODULE := $(TEST)

include $(shell cocotb-config --makefiles)/Makefile.sim

hdltest: sim

else

clean:
	$(RM) results.xml dump.vcd dump.fst
	$(RM) -r sim_build

endif

endif

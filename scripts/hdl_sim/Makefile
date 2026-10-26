# Block-level cocotb + Verilator tests.
#
# From the repository root:
#   make hdltest.<name>   MODULE=test_<name>  SIM=verilator
#   make hdltest          every test_*.py, or a clean no-op if none exist
#
# cocotb 2 reads COCOTB_TEST_MODULES. The top-level makefile still passes
# MODULE (the cocotb 1 name); this file copies it across.
#
# A block test is scripts/hdl_sim/test_<name>.py plus optional <name>.mk
# setting VERILOG_SOURCES and, if needed, COCOTB_TOPLEVEL (default: <name>).
# dac_top.mk / test_dac_top.py elaborate the DAC subsystem top.
# UVM / system tests do not belong here.
#
# Verilator itself is a local install (cocotb wants 5.036+). It is not a
# Python dependency. `make hdltest` does not invoke it when no test_*.py
# files are present. cocotb is installed with `uv sync`.

REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../..)

# GNU make does not apply `export PATH` to $(shell) in this same process,
# and cocotb's Makefile.sim runs `cocotb-config` that way. Restart once so
# .venv/bin is already on PATH. Command-line variables (MODULE, SIM, ...)
# are forwarded through MAKEFLAGS.
ifndef HDL_SIM_REEXEC
export PATH := $(REPO_ROOT)/.venv/bin:$(PATH)

.PHONY: _hdl_sim_reexec
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

ifneq ($(strip $(MODULE)),)
COCOTB_TEST_MODULES ?= $(MODULE)
endif

TEST_MODULES := $(patsubst %.py,%,$(wildcard test_*.py))

ifeq ($(strip $(COCOTB_TEST_MODULES)),)

ifeq ($(strip $(TEST_MODULES)),)
all:
	@echo "[hdl_sim] No block tests yet. Add test_<name>.py and run make hdltest.<name>."
else
all:
	@set -e; \
	for mod in $(TEST_MODULES); do \
		echo "[hdl_sim] $$mod"; \
		$(MAKE) --no-print-directory HDL_SIM_REEXEC=1 MODULE="$$mod" SIM="$(SIM)"; \
	done
endif

else

HDLTEST_STEM := $(patsubst test_%,%,$(COCOTB_TEST_MODULES))
-include $(HDLTEST_STEM).mk
COCOTB_TOPLEVEL ?= $(HDLTEST_STEM)

# Include cocotb's simulator makefile only when a simulation was asked
# for. `make clean` must succeed on a machine that does not have Verilator.
SIM_GOALS := $(if $(MAKECMDGOALS),$(filter-out clean help,$(MAKECMDGOALS)),sim)
ifneq ($(strip $(SIM_GOALS)),)

ifeq ($(wildcard $(COCOTB_TEST_MODULES).py),)
$(error No $(COCOTB_TEST_MODULES).py in scripts/hdl_sim (make hdltest.$(HDLTEST_STEM)))
endif

ifeq ($(strip $(VERILOG_SOURCES)),)
$(error hdltest.$(HDLTEST_STEM) has no VERILOG_SOURCES. Add $(HDLTEST_STEM).mk or pass VERILOG_SOURCES= on the command line. This tree does not ship a dummy DUT)
endif

include $(shell cocotb-config --makefiles)/Makefile.sim

endif
endif

.PHONY: all clean
clean::
	@rm -rf sim_build results.xml dump.vcd dump.fst

endif

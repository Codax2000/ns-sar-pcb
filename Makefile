# ---------------------------------------------------------------------------
# PeakRDL Register Generation Makefile
# ---------------------------------------------------------------------------

# Python Executable and Script
PYTHON       := python3
MKDOCS       := mkdocs
REG_SCRIPT   := ./scripts/registers.py 
IMG_SCRIPT   := ./scripts/diagrams.py

# RDL Source Specs
UDP_SPEC     := ./hdl_design/hdl_design.srcs/registers/regblock_udps.rdl
DAC_SPEC     := ./hdl_design/hdl_design.srcs/registers/dac_registers.rdl
ADC_SPEC     := ./hdl_design/hdl_design.srcs/registers/adc_registers.rdl
TOP_SPEC     := ./hdl_design/hdl_design.srcs/registers/chip_top.rdl

# Output Paths
DAC_RTL_DIR  := ./hdl_design/hdl_design.srcs/rtl/registers/dac
ADC_RTL_DIR  := ./hdl_design/hdl_design.srcs/rtl/registers/adc
TOP_HTML_DIR := ./docs/docs/chip_top
DOCS_IMG_DIR := ./docs/docs/img
UVM_PKG      := ./hdl_design/hdl_design.srcs/dv/axi_top_env/chip_regs_dv_pkg.sv
ADC_SYNC     := ./hdl_design/hdl_design.srcs/rtl/registers/adc/adc_reg_sync.sv
C_HEADER     := ./software/firmware/src/registers/chip_top_registers.h

.PHONY: gen clean

gen: clean
	@mkdir -p $(DAC_RTL_DIR) $(ADC_RTL_DIR) $(TOP_HTML_DIR) \
		$(dir $(UVM_PKG)) $(dir $(C_HEADER)) $(DOCS_IMG_DIR)
	@$(PYTHON) $(REG_SCRIPT) \
		--udp-spec $(UDP_SPEC) \
		--dac-spec $(DAC_SPEC) \
		--adc-spec $(ADC_SPEC) \
		--top-spec $(TOP_SPEC) \
		--dac-rtl  $(DAC_RTL_DIR) \
		--adc-rtl  $(ADC_RTL_DIR) \
		--top-html $(TOP_HTML_DIR) \
		--uvmpkg   $(UVM_PKG) \
		--sync     $(ADC_SYNC) \
		--cheader  $(C_HEADER)
	@$(PYTHON) $(IMG_SCRIPT)
	@echo "[Makefile] Building documentation site..."
	@cd docs; $(MKDOCS) build; cd ..;
	@echo "[Makefile] Done."

deploy:
	cd docs; $(MKDOCS) gh-deploy; cd ..;
	@echo "[Makefile] Done."

clean:
	@echo "[Makefile] Cleaning generated files..."
	@rm -rf $(DAC_RTL_DIR)
	@rm -rf $(ADC_RTL_DIR)
	@rm -rf $(TOP_HTML_DIR)
	@rm -f $(UVM_PKG)
	@rm -f $(ADC_SYNC)
	@rm -f $(C_HEADER)
	@rm -rf $(DOCS_IMG_DIR)
	@rm -rf ./docs/site
	@rm -rf ./scripts/img
	@rm -rf ./scripts/__pycache__
	@rm -rf .aider*
	@echo "[Makefile] Done."
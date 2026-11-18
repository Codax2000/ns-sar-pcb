# ---------------------------------------------------------------------------
# PeakRDL Register Generation Makefile
# ---------------------------------------------------------------------------

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
PYUVM_REG    := ./scripts/hdl_sim/chip_regs.py
UVM_PKG      := ./hdl_design/hdl_design.srcs/dv/chip_top_regs/chip_regs_dv_pkg.sv
ADC_SYNC     := ./hdl_design/hdl_design.srcs/rtl/registers/adc/adc_reg_sync.sv
C_HEADER     := ./software/firmware/src/registers/chip_top_registers.h

.PHONY: gen clean diagrams doc serve deploy

gen: clean
	@mkdir -p $(DAC_RTL_DIR) $(ADC_RTL_DIR) $(dir $(UVM_PKG)) $(DOCS_IMG_DIR)
	peakrdl regblock $(UDP_SPEC) $(DAC_SPEC) \
		-o $(DAC_RTL_DIR) \
		--cpuif passthrough \
		--module-name dac_regs_mod \
		--hwif-report \
		--rt-read-response
	peakrdl regblock $(UDP_SPEC) $(ADC_SPEC) \
		-o $(ADC_RTL_DIR) \
		--cpuif passthrough \
		--module-name adc_regs_mod \
		--hwif-report \
		--rt-read-response
	peakrdl uvm $(UDP_SPEC) $(ADC_SPEC) $(DAC_SPEC) $(TOP_SPEC) \
		-t chip_top \
		-o $(UVM_PKG) \
		--use-factory
	peakrdl pyuvm $(UDP_SPEC) $(ADC_SPEC) $(DAC_SPEC) $(TOP_SPEC) \
		-t chip_top \
		-o $(PYUVM_REG)
	@python $(IMG_SCRIPT)
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
	@rm -rf ./scripts/models/__pycache__
	@$(MAKE) -C scripts/hdl_sim clean
	@rm -rf .aider*
	@echo "[Makefile] Done."

# Schemdraw figures referenced by the Sphinx sources.
# Written to docs/_static/img/ (gitignored).
diagrams:
	python $(IMG_SCRIPT)

# HTML docs. Pushes to main publish the same build via .github/workflows/docs.yml.
doc: diagrams
	python -m sphinx.cmd.build -b html docs docs/_build/html

serve:
	python -m http.server --directory docs/_build/html

%.sim:
	$(MAKE) -C scripts/hdl_sim $*.sim SIM=verilator

# Local publish of docs/_build/html to the gh-pages branch.
deploy:
	@ghp-import -m "Update documentation" -b gh-pages docs/_build/html --push --no-jekyll
	@echo "[Makefile] Deployed to GitHub Pages. New site should be visible in a few minutes."

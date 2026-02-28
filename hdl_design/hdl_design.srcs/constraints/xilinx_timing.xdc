################################################################################
# Global Timing Constraints for NS-SAR-PCB
# Author: Codax2000 (Ghostwritten)
################################################################################

# 1. Primary Clock Definitions
# ------------------------------------------------------------------------------
# System Clock (Assuming a 100MHz oscillator on the PCB as per oscillator_agent)
create_clock -period 10.000 -name sys_clk [get_ports sys_clk_p]

# SPI Clock (Parametrized: 25MHz)
# Note: SPI is usually source-synchronous from the MCU/Master
create_clock -period 40.000 -name sclk [get_ports spi_sclk]

# 2. SPI Input/Output Constraints
# ------------------------------------------------------------------------------
# Setup and Hold for SPI signals relative to SCLK
# Assuming a 5ns setup/hold requirement for the external SPI Master
set_input_delay -clock [get_clocks sclk] -max 10.000 [get_ports {spi_mosi spi_ss_n}]
set_input_delay -clock [get_clocks sclk] -min 2.000  [get_ports {spi_mosi spi_ss_n}]

set_output_delay -clock [get_clocks sclk] -max 10.000 [get_ports spi_miso]
set_output_delay -clock [get_clocks sclk] -min 2.000  [get_ports spi_miso]

# 3. Asynchronous SAR Logic Constraints
# ------------------------------------------------------------------------------
# The ADC_CTRL.DELAY_LINE_CTRL [3:0] register controls an asynchronous delay line.
# In a standard industry async SAR, the internal "Done" signals and bit-settling 
# paths are not phase-aligned to sys_clk.

# Define the Asynchronous SAR paths as false paths to prevent Vivado from 
# trying to meet synchronous timing on the delay-line tapped loops.
set_false_path -from [get_cells -hierarchical *sar_logic_inst/async_delay_reg*]
set_false_path -to [get_cells -hierarchical *sar_logic_inst/comparator_trigger_reg*]

# 4. Clock Domain Crossing (CDC)
# ------------------------------------------------------------------------------
# As seen in your scripts, you use PeakRDL to generate CDC sync logic.
# These registers (NFFT_CTRL, OSR, etc.) move from the SPI (SCLK) domain 
# to the ADC System Domain.

# Tag the CDC paths as asynchronous to allow the synchronizers to handle them.
set_clock_groups -asynchronous -group [get_clocks sys_clk] -group [get_clocks sclk]

# Specific constraint for the Start Conversion pulse which triggers the Main FSM
set_false_path -from [get_cells -hierarchical *ADC_CTRL_reg/START_CONVERSION_reg*] -to [get_cells -hierarchical *main_fsm_inst/start_sync_reg*]

# 5. Memory and DRP Constraints
# ------------------------------------------------------------------------------
# CLKGEN_DRP_CONFIG uses the Xilinx Dynamic Reconfiguration Port.
# This port typically runs on a stable reference clock (sys_clk).
set_max_delay -from [get_clocks sclk] -to [get_clocks sys_clk] 10.000
set_max_delay -from [get_clocks sys_clk] -to [get_clocks sclk] 10.000

# 6. Physical Floorplanning (Inferred from scripts/diagrams.py)
# ------------------------------------------------------------------------------
# Placing the ADC Digital Core near the FPGA-to-PCB Analog headers 
# to minimize jitter on the SAR switching signals.
# create_pblock pblock_ADC_CORE
# add_cells_to_pblock [get_pblocks pblock_ADC_CORE] [get_cells -hierarchical *dig_core_inst*]
# resize_pblock [get_pblocks pblock_ADC_CORE] -add {SLICE_X0Y0:SLICE_X20Y50}
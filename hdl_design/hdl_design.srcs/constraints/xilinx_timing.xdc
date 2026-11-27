################################################################################
# Timing constraints for chip_top (Arty Z7)
#
# sysclk is created in xilinx_placement.xdc (sys_clk_pin, 120 MHz).
# Host SPI scl is a fully independent external clock; there is no
# period/phase relationship to sysclk. Prefer set_max_delay over
# set_clock_groups -asynchronous so Vivado still bounds the CDC paths
# through the SPI synchronizers instead of ignoring them entirely.
################################################################################

# External SPI serial clock (host master). Period is a placeholder budget.
create_clock -period 40.000 -name spi_scl [get_ports scl]

# Bound datapath delay between the system and SPI clock domains.
set_max_delay -datapath_only -from [get_clocks sys_clk_pin] -to [get_clocks spi_scl] 8.333

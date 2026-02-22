/**
Class: adc_env_cfg

Configuration class for the ADC environment.
*/
import uvm_pkg::*;
`include "uvm_macros.svh"

class adc_env_cfg extends uvm_object;

    `uvm_object_utils(adc_env_cfg)

    function new(name);
        super.new(name);
    endfunction

    // Variable: vif_clk
    // Virtual interface for the system clock agent.
    virtual oscillator_if vif_clk;

    // Variable: vif_reset
    // Virtual interface for the reset signal bus.
    virtual bit_bus_if #(.WIDTH(1)) vif_reset;

    // Variable: vif_spi
    // Virtual interface for the SPI agent.
    virtual spi_if vif_spi;

    // Variable: vif_adc
    // Virtual interface for the digital portion of the ADC input bus, which
    // is a UVM-MS extension of <oscillator_agent>.
    virtual oscillator_if vif_adc;

    // Variable: vproxy_adc
    // Proxy used to monitor ADC input amplitude.
    sine_proxy vproxy_adc;

    // Variable: checks_enable
    // If 1, enables any defined internal SVA checks on the agents.
    bit checks_enable;

    // Variable: coverage_enable
    // If 1, enables building and collection of any coverage defined by the agents or the env.
    bit coverage_enable;

    // Variable: spi_clk_frequency
    // Frequency in *Hz* that the SPI clock must run at. 10 kHz probably good for implementation,
    // 2 MHz good for early simulation.
    real spi_clk_frequency;

    // Variable: system_clk_frequency
    // The frequency in *Hz* that the system clock must run at. Eventually, set to be the same
    // speed as they PCB oscillator and assume an internal PLL, so maybe 5-12 MHz is good.
    real system_clk_frequency;

    // Variable: reset_duration
    // The duration in seconds that the reset pulse will last at the start of simulation.
    real reset_duration;

endclass
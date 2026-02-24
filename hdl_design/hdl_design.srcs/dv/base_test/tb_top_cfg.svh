/**
Class: tb_top_cfg

Contains virtual interfaces and proxies from the test module.
*/
class tb_top_cfg extends uvm_object;

    `uvm_object_utils(tb_top_cfg)

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

    // Variable: vif_status
    // The status interface used to monitor things at the analog-digital boundary.
    virtual status_if vif_status;

    function new (string name = "tb_top_cfg");
        super.new(name);
    endfunction

endclass
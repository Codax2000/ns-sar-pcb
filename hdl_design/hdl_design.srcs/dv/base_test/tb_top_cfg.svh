/**
Class: tb_top_cfg

Contains virtual interfaces and proxies from the test module.
*/
class tb_top_cfg extends uvm_object;

    `uvm_object_utils(tb_top_cfg)

    // Variable: vif_clk
    // Virtual interface for the system clock agent.
    // virtual oscillator_if vif_clk;

    // Variable: vif_reset
    // Virtual interface for the reset signal bus.
    // virtual bit_bus_if #(.WIDTH(1)) vif_reset;

    // Variable: vif_adc_spi
    // Virtual interface for the SPI agent.
    // virtual spi_if vif_adc_spi;

    // Variable: vif_dac_spi
    // Virtual interface for the SPI agent.
    virtual spi_if vif_dac_spi;

    // Variable: vif_status
    // The status interface used to monitor things at the analog-digital boundary.
    // virtual status_if vif_status;

    function new (string name = "tb_top_cfg");
        super.new(name);
    endfunction

endclass
/**
Class: spi_agent_cfg

Configuration object for the SPI agent. In addition to boilerplate agent flags,
also contains SPI interface and SPI clock speed.
*/
class spi_agent_cfg extends uvm_object;

    `uvm_object_utils(spi_agent_cfg)

    function new(name = "spi_agent_cfg");
        super.new(name);
    endfunction

    // Variable: vif
    // Virtual SPI interface.
    virtual spi_if vif;

    // Variable: clk_speed_hz
    // The SPI clock speed at which transactions will be run. Typical values likely 100kHz - 5 MHz.
    real clk_speed_hz;

    uvm_active_passive_enum is_active;
    rand bit                checks_enable;
    rand bit                coverage_enable;

endclass
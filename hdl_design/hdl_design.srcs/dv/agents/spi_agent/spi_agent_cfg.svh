/*
Class: spi_agent_cfg

Configuration object for the SPI agent. In addition to boilerplate agent flags,
also contains the SPI interface handle and SPI clock speed.
*/
class spi_agent_cfg extends uvm_object;

    `uvm_object_utils(spi_agent_cfg)

    /*
    Variable: is_active
    Determines whether the agent is UVM_ACTIVE (creates sequencer and driver)
    or UVM_PASSIVE (only creates the monitor).
    */
    uvm_active_passive_enum is_active = UVM_ACTIVE;

    /*
    Variable: checks_enable
    Doulos Easier UVM standard flag to enable or disable protocol checkers/assertions.
    */
    bit checks_enable = 1'b1;

    /*
    Variable: coverage_enable
    Doulos Easier UVM standard flag to enable or disable functional coverage.
    */
    bit coverage_enable = 1'b0;

    /*
    Variable: clk_speed_hz
    The SPI clock speed at which transactions will be run. 
    Typical values range from 100_000 (100kHz) to 5_000_000 (5MHz).
    */
    int clk_speed_hz = 1_000_000;

    /*
    Variable: vif
    Virtual interface handle linking the driver and monitor to the physical SPI bus.
    */
    virtual spi_if vif;

    function new(string name = "spi_agent_cfg");
        super.new(name);
    endfunction : new

endclass : spi_agent_cfg
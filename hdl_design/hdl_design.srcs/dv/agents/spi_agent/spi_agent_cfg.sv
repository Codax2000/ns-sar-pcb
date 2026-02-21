class spi_agent_cfg extends uvm_object;

    `uvm_object_utils(spi_agent_cfg)

    function new(name = "spi_agent_cfg");
        super.new(name);
    endfunction

    virtual spi_if vif;
    real clk_speed_hz;

    uvm_active_passive_enum is_active;
    rand bit                checks_enable;
    rand bit                coverage_enable;

endclass
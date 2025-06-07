class spi_agent_cfg extends uvm_object;

    `uvm_object_utils(spi_agent_cfg)

    function new(name = "spi_agent_cfg");
        super.new(name);
    endfunction

    virtual if_spi vif;
    int nfft;
    int speed;

    uvm_active_passive_enum is_active;
    rand bit                checks_enable;
    rand bit                coverage_enable;

    rand bit CPHA;
    rand bit CPOL;

endclass
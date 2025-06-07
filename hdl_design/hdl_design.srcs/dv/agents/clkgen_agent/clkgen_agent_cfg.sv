class clkgen_agent_cfg extends uvm_object;

    `uvm_object_utils(clkgen_agent_cfg)

    function new(name = "clkgen_agent_cfg");
        super.new(name);
    endfunction

    int sys_clk;

    virtual if_clkgen vif;

    uvm_active_passive_enum is_active;
    bit                     checks_enable;
    bit                     coverage_enable;

endclass
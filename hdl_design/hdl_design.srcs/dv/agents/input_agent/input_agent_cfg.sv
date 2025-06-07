class input_agent_cfg extends uvm_object;

    `uvm_object_utils(input_agent_cfg)

    function new(name = "input_agent_cfg");
        super.new(name);
    endfunction

    int nfft;
    int osr;
    real fs;
    real vdd;

    virtual if_input vif;

    uvm_active_passive_enum is_active;
    bit                     checks_enable;
    bit                     coverage_enable;

endclass
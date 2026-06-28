class axi4lite_config extends uvm_object;
    `uvm_object_utils(axi4lite_config)

    // Default topology setup
    uvm_active_passive_enum is_active = UVM_ACTIVE;

    // Custom configuration parameters
    int clk_speed_mhz = 100; // Default AXI clock speed
    
    // Virtual Interface Handle
    virtual axi4_lite_if vif;

    bit coverage_enable;

    bit checks_enable;

    function new(string name = "axi4lite_config");
        super.new(name);
    endfunction
endclass
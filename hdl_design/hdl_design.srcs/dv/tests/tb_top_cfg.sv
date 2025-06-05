class tb_top_cfg extends uvm_object;

    `uvm_object_utils(tb_top_cfg)

    virtual if_spi vif_spi;
    virtual if_clkgen vif_clkgen;
    virtual if_input vif_input;
    virtual if_status vif_status;

    function new (string name = "tb_top_cfg");
        super.new(name);
    endfunction

endclass
class tb_env extends uvm_env;

    `uvm_component_utils (tb_env)

    spi_agent spi;
    clk_rst_gen_agent clkgen;
    input_agent signal_gen;

    virtual if_spi vif_spi;
    virtual if_clkgen vif_clkgen;
    virtual if_input vif_input;
    virtual if_status vif_status;

    reg_env ral;

    function new(string name = "tb_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);
        spi = spi_agent::type_id::create("spi", this);
        clkgen = clk_rst_gen_agent::type_id::create("clkgen", this);
        signal_gen = input_agent::type_id::create("signal_gen", this);
        ral = reg_env::type_id::create("ral", this);
        uvm_reg::include_coverage ("*", UVM_CVR_ALL);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        ral.agent = spi;
        ral.ral_model.default_map.set_sequencer(spi.sequencer);
        // TODO: if using a predictor, connect the agent analysis port to the predictor bus

        // connect interfaces
        if (!uvm_config_db #(virtual if_clkgen)::get(this, "", "vif_clkgen", vif_clkgen))
            `uvm_fatal("ENV", "Could not find CLKGEN virtual interface")
        if (!uvm_config_db #(virtual if_spi)::get(this, "", "vif_spi", vif_spi))
            `uvm_fatal("ENV", "Could not find SPI virtual interface")
        if (!uvm_config_db #(virtual if_input)::get(this, "", "vif_input", vif_input))
            `uvm_fatal("ENV", "Could not find INPUT virtual interface")
        if (!uvm_config_db #(virtual if_status)::get(this, "", "vif_status", vif_status))
            `uvm_fatal("ENV", "Could not find STATUS virtual interface")
        
        uvm_config_db #(virtual if_clkgen)::set(this, "clkgen", "vif", vif_clkgen);
        uvm_config_db #(virtual if_spi)::set(this, "spi", "vif", vif_spi);
        uvm_config_db #(virtual if_input)::set(this, "signal_gen", "vif", vif_input);
        
    endfunction

endclass
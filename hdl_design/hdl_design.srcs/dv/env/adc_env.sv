class adc_env extends uvm_env;

    `uvm_component_utils (adc_env)

    spi_agent spi;
    clkgen_agent clkgen;
    input_agent signal_gen;

    adc_env_cfg i_env_cfg;

    reg_env ral;

    function new(string name = "adc_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(adc_env_cfg)::get(this, "", "cfg", i_env_cfg))
            `uvm_fatal("ENV", "Could not attach environment config")

        uvm_config_db #(virtual if_spi)   ::set(this, "spi", "vif", i_env_cfg.vif_spi);
        uvm_config_db #(virtual if_clkgen)::set(this, "clkgen", "vif", i_env_cfg.vif_clkgen);
        uvm_config_db #(virtual if_input) ::set(this, "signal_gen", "vif", i_env_cfg.vif_input);

        spi = spi_agent::type_id::create("spi", this);
        clkgen = clkgen_agent::type_id::create("clkgen", this);
        signal_gen = input_agent::type_id::create("signal_gen", this);
        ral = reg_env::type_id::create("ral", this);

        uvm_reg::include_coverage ("*", UVM_CVR_ALL);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        ral.agent = spi;
        ral.ral_model.default_map.set_sequencer(spi.sequencer, ral.adapter);
        spi.monitor.mon_analysis_port.connect(ral.spi_predictor.bus_in);
    endfunction

endclass
`timescale 1ns/1ps

class adc_env extends uvm_env;

    `uvm_component_utils (adc_env)

    spi_agent spi;
    spi_agent_cfg spi_cfg;
    clkgen_agent clkgen;
    clkgen_agent_cfg clkgen_cfg;
    input_agent signal_gen;
    input_agent_cfg signal_gen_cfg;

    adc_env_cfg i_env_cfg;

    reg_env ral;

    function new(string name = "adc_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(adc_env_cfg)::get(this, "", "cfg", i_env_cfg))
            `uvm_fatal("ENV", "Could not attach environment config")
        
        create_configs();

        uvm_config_db #(input_agent_cfg)::set(this, "signal_gen", "cfg", signal_gen_cfg);
        uvm_config_db #(spi_agent_cfg)        ::set(this, "spi", "cfg", spi_cfg);
        uvm_config_db #(clkgen_agent_cfg)::set(this, "clkgen", "cfg", clkgen_cfg);

        spi = spi_agent::type_id::create("spi", this);
        clkgen = clkgen_agent::type_id::create("clkgen", this);
        signal_gen = input_agent::type_id::create("signal_gen", this);
        ral = reg_env::type_id::create("ral", this);

        uvm_reg::include_coverage ("*", UVM_CVR_ALL);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        ral.ral_model.default_map.set_sequencer(spi.sequencer, ral.adapter);
        spi.monitor.mon_analysis_port.connect(ral.spi_predictor.bus_in);
    endfunction

    virtual function void create_configs();
        spi_cfg = new("spi_cfg");
        spi_cfg.vif = i_env_cfg.vif_spi;
        spi_cfg.nfft = i_env_cfg.nfft;
        spi_cfg.speed = i_env_cfg.spi_clk;
        spi_cfg.is_active = UVM_ACTIVE;
        spi_cfg.checks_enable = i_env_cfg.checks_enable;
        spi_cfg.coverage_enable = i_env_cfg.coverage_enable;
        spi_cfg.randomize();

        signal_gen_cfg = new("signal_gen_cfg");
        signal_gen_cfg.is_active = UVM_ACTIVE;
        signal_gen_cfg.nfft = i_env_cfg.nfft;
        signal_gen_cfg.fs = i_env_cfg.sys_clk / (4 * i_env_cfg.clk_div);
        signal_gen_cfg.osr = i_env_cfg.osr;
        signal_gen_cfg.vdd = i_env_cfg.vdd;
        signal_gen_cfg.vif = i_env_cfg.vif_input;
        signal_gen_cfg.checks_enable = i_env_cfg.checks_enable;
        signal_gen_cfg.coverage_enable = i_env_cfg.coverage_enable;

        clkgen_cfg = new("clkgen_cfg");
        clkgen_cfg.is_active = UVM_ACTIVE;
        clkgen_cfg.checks_enable = i_env_cfg.checks_enable;
        clkgen_cfg.coverage_enable = i_env_cfg.coverage_enable;
        clkgen_cfg.sys_clk = i_env_cfg.sys_clk;
        clkgen_cfg.vif = i_env_cfg.vif_clkgen;
    endfunction

endclass
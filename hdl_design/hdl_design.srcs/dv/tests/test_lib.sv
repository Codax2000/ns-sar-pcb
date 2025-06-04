class base_test extends uvm_test;

    `uvm_component_utils(base_test)

    tb_env env;
    top_cfg i_top_cfg;
    env_cfg i_env_cfg;

    virtual if_status vif_status;

    function new (string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(top_cfg)::get(this, "*", "top_cfg", i_top_cfg))
            `uvm_fatal("TB_TOP", "Could not attach top-level configuration")

        i_env_cfg = new("i_env_cfg");
        i_env_cfg.randomize();
        i_env_cfg.vif_spi = i_top_cfg.vif_spi;
        i_env_cfg.vif_clkgen = i_top_cfg.vif_clkgen;
        i_env_cfg.vif_input = i_top_cfg.vif_input;
        vif_status = i_top_cfg.vif_status;

        uvm_config_db #(env_cfg)::set(this, "env", "cfg", i_env_cfg);

        env = tb_env::type_id::create("env", this);
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
    endfunction

    virtual task reset_phase(uvm_phase phase);
        start_clk_seq seq;

        `uvm_info("RESET_PHASE", "Resetting DUT", UVM_MEDIUM)
        phase.raise_objection(this);

        seq = start_clk_seq::type_id::create("seq");
        seq.start(env.clkgen.sequencer);

        `uvm_info("RESET_PHASE", "DUT Successfully reset", UVM_MEDIUM)
        phase.drop_objection(this);

    endtask

    // virtual task configure_phase (uvm_phase phase);
    //     ral_registers ral;
    //     uvm_status_e status;
    //     logic [3:0] rdata;

    //     `uvm_info("CONFIG_PHASE", "Configuring DUT", UVM_MEDIUM)
    //     ral = env.ral.ral_model;

    //     phase.raise_objection(this);
    //     cfg.print();

    //     // write NFFT
    //     ral.nfft_pow.write(status, cfg.nfft_power);

    //     // set OSR and DWA and then update()
    //     ral.osr_dwa.osr.set(cfg.osr_power);
    //     ral.osr_dwa.dwa_enable.set(cfg.is_dwa);
    //     ral.update(status);

    //     // write CLKDIV
    //     ral.sample_clk_div.write(status, cfg.clk_div);

    //     // TODO: read registers back to ensure correct config
    //     // TODO: read status register to ensure the DUT is ready

    //     phase.drop_objection(this);
    // endtask

endclass

// class test_register_read_write extends base_test;

//     // during run phase, write a random register

//     // read it back

//     // should match up with RAL model

// endclass

// class test_random_conversion extends base_test;

//     // drive a bunch of random values onto the input and convert nfft
//     // different values (nfft should be a random number written to the nfft
//     // register at start of test)

// endclass

// class test_dwa extends base_test;

//     // during build phase, override scoreboard to use a noise-based model instead
//     // of a register-based one

//     // write nfft to be a random power of 2
//     // set DWA to be off
//     // convert, compare SNDR/SFDR to ref model (should be close, within 1 dB)
//     // turn DWA on
//     // convert same signal again, compare SNDR/SFDR to ref model (should be
//     // within 1 dB also)

// endclass
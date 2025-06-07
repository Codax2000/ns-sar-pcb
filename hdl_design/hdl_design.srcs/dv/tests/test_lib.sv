import adc_env_pkg     ::*;
import clkgen_agent_pkg::*;
import input_agent_pkg ::*;
import uvm_pkg         ::*;
`include "uvm_macros.svh"

class base_test extends uvm_test;

    `uvm_component_utils(base_test)

    adc_env env;
    tb_top_cfg i_top_cfg;
    adc_env_cfg i_env_cfg;

    virtual if_status vif_status;

    bit checks_enable;
    bit coverage_enable;

    uvm_status_e status;

    function new (string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
        checks_enable = 1'b0;
        coverage_enable = 1'b0; // these can be overridden in child constructors
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(tb_top_cfg)::get(this, "*", "tb_top_cfg", i_top_cfg))
            `uvm_fatal("TB_TOP", "Could not attach top-level configuration")

        i_env_cfg = new("i_env_cfg");
        i_env_cfg.randomize();
        i_env_cfg.vif_spi = i_top_cfg.vif_spi;
        i_env_cfg.vif_clkgen = i_top_cfg.vif_clkgen;
        i_env_cfg.vif_input = i_top_cfg.vif_input;
        vif_status = i_top_cfg.vif_status;

        i_env_cfg.checks_enable = checks_enable;
        i_env_cfg.coverage_enable = coverage_enable;

        uvm_config_db #(adc_env_cfg)::set(this, "env", "cfg", i_env_cfg);

        env = adc_env::type_id::create("env", this);
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
    endfunction

    virtual task reset_phase(uvm_phase phase);
        start_clk_seq clk_seq;
        drive_sine_wave_seq input_seq;

        `uvm_info("RESET_PHASE", "Resetting DUT", UVM_MEDIUM)
        phase.raise_objection(this);

        clk_seq = start_clk_seq::type_id::create("clk_seq");
        input_seq = drive_sine_wave_seq::type_id::create("input_seq");

        fork
            clk_seq.start(env.clkgen.sequencer);
            input_seq.start(env.signal_gen.sequencer);
        join

        `uvm_info("RESET_PHASE", "DUT Successfully reset and sine wave being generated", UVM_MEDIUM)
        phase.drop_objection(this);

    endtask

    virtual task configure_phase (uvm_phase phase);
        ral_registers ral;
        logic [3:0] rdata;

        `uvm_info("CONFIG_PHASE", "Configuring DUT", UVM_MEDIUM)
        ral = env.ral.ral_model;

        phase.raise_objection(this);
        i_env_cfg.print();

        // write NFFT
        ral.nfft_pow.write(status, i_env_cfg.nfft_power);

        // set OSR and DWA and then update()
        ral.osr_dwa.osr.set(i_env_cfg.osr_power);
        ral.osr_dwa.dwa_enable.set(i_env_cfg.is_dwa);
        ral.update(status);

        // write CLKDIV
        ral.sample_clk_div.write(status, i_env_cfg.clk_div);

        ral.print();

        // mirror values back to make sure they are what we just wrote
        ral.nfft_pow.predict(i_env_cfg.nfft_power);
        ral.nfft_pow.mirror(status, UVM_CHECK);

        ral.osr_dwa.predict({i_env_cfg.osr_power, i_env_cfg.is_dwa});
        ral.osr_dwa.mirror(status, UVM_CHECK);

        ral.sample_clk_div.predict(i_env_cfg.clk_div);
        ral.sample_clk_div.mirror(status, UVM_CHECK);

        ral.status.predict(4'h0);
        ral.status.mirror(status, UVM_CHECK);

        `uvm_info("CONFIG_PHASE", "Finished Configuring DUT", UVM_MEDIUM)
        phase.drop_objection(this);
    endtask

    virtual task main_phase(uvm_phase phase);
        `uvm_info("MAIN_PHASE", "Running randomized conversion test", UVM_MEDIUM)
        begin_conversion();
        allow_conversion_to_end();
        read_conversion_results();
        `uvm_info("MAIN_PHASE", "Finished random conversion test", UVM_MEDIUM)
    endtask

    virtual task post_main_phase(uvm_phase phase);
        `uvm_info("POST_MAIN_PHASE", "Checking device status registers", UVM_MEDIUM)

        env.ral.ral_model.status.predict(4'h0);
        env.ral.ral_model.status.mirror(status, UVM_CHECK);

        `uvm_info("POST_MAIN_PHASE", "Status checking finished", UVM_MEDIUM)
    endtask

    task begin_conversion();
        ral_registers ral;
        ral = env.ral.ral_model;
        ral.status.begin_sample.set(1'b1);
        ral.update(status);
    endtask

    task read_conversion_results();
        ral_registers ral;
        ral = env.ral.ral_model;
        ral.status.read_mem.set(1'b1);
        ral.update(status);
    endtask

    task allow_conversion_to_end();
        wait (vif_status.fsm_convert_status == 2'b00);
    endtask

endclass

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
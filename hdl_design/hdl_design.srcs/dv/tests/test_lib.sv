import uvm_pkg         ::*;
`include "uvm_macros.svh"

import adc_env_pkg     ::*;
import clkgen_agent_pkg::*;
import input_agent_pkg ::*;

class base_test extends uvm_test;

    `uvm_component_utils(base_test)

    adc_env     env;
    tb_top_cfg  i_top_cfg;
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
        randomize_config();
        i_env_cfg.vif_spi = i_top_cfg.vif_spi;
        i_env_cfg.vif_clkgen = i_top_cfg.vif_clkgen;
        i_env_cfg.vif_input = i_top_cfg.vif_input;
        vif_status = i_top_cfg.vif_status;

        i_env_cfg.checks_enable = checks_enable;
        i_env_cfg.coverage_enable = coverage_enable;

        uvm_config_db #(adc_env_cfg)::set(this, "env", "cfg", i_env_cfg);

        env = adc_env::type_id::create("env", this);
    endfunction

    virtual function int randomize_config();
        return i_env_cfg.randomize();
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
        
        wait(vif_status.rst_b == 1);

        `uvm_info("RESET_PHASE", "DUT Successfully reset and sine wave being generated", UVM_MEDIUM)
        phase.drop_objection(this);

    endtask

    virtual task configure_phase (uvm_phase phase);
        dut_memory ral;
        logic [3:0] rdata;

        `uvm_info("CONFIG_PHASE", "Configuring DUT", UVM_MEDIUM)
        ral = env.ral.ral_model;

        phase.raise_objection(this);
        i_env_cfg.print();

        // write config to device
        set_field("NFFT_POWER", i_env_cfg.nfft_power);
        set_field("DWA_EN", i_env_cfg.dwa_en);
        set_field("OSR_POWER", i_env_cfg.osr_power);
        set_field("N_SH_TOTAL_CYCLES", i_env_cfg.n_sh_total_cycles);
        set_field("N_SH_ACTIVE_CYCLES", i_env_cfg.n_sh_active_cycles);
        set_field("N_BOTTOM_PLATE_ACTIVE_CYCLES", i_env_cfg.n_bottom_plate_active_cycles);
        set_field("N_SAR_CYCLES", i_env_cfg.n_sar_cycles);
        set_field("N_INT1_TOTAL_CYCLES", i_env_cfg.n_int1_total_cycles);
        set_field("N_INT1_ACTIVE_CYCLES", i_env_cfg.n_int1_active_cycles);
        set_field("N_INT2_TOTAL_CYCLES", i_env_cfg.n_int2_total_cycles);
        set_field("N_INT2_ACTIVE_CYCLES", i_env_cfg.n_int2_active_cycles);
        update_reg();
        
        ral.print();

        `uvm_info("CONFIG_PHASE", "Reading back registers to make sure write data worked", UVM_MEDIUM);

        // TODO: mirror values back to make sure they are what we just wrote
        check_field("NFFT_POWER", i_env_cfg.nfft_power);
        check_field("DWA_EN", i_env_cfg.dwa_en);
        check_field("OSR_POWER", i_env_cfg.osr_power);
        check_field("N_SH_TOTAL_CYCLES", i_env_cfg.n_sh_total_cycles);
        check_field("N_SH_ACTIVE_CYCLES", i_env_cfg.n_sh_active_cycles);
        check_field("N_BOTTOM_PLATE_ACTIVE_CYCLES", i_env_cfg.n_bottom_plate_active_cycles);
        check_field("N_SAR_CYCLES", i_env_cfg.n_sar_cycles);
        check_field("N_INT1_TOTAL_CYCLES", i_env_cfg.n_int1_total_cycles);
        check_field("N_INT1_ACTIVE_CYCLES", i_env_cfg.n_int1_active_cycles);
        check_field("N_INT2_TOTAL_CYCLES", i_env_cfg.n_int2_total_cycles);
        check_field("N_INT2_ACTIVE_CYCLES", i_env_cfg.n_int2_active_cycles);

        `uvm_info("CONFIG_PHASE", "Finished Configuring DUT", UVM_MEDIUM)
        phase.drop_objection(this);
    endtask

    task write_field(string name, uvm_reg_data_t value);
        uvm_reg_field field_to_write;
        field_to_write = env.ral.ral_model.get_field_by_name(name);
        field_to_write.write(status, value);
    endtask

    task set_field(string name, uvm_reg_data_t value);
        uvm_reg_field field_to_set;
        field_to_set = env.ral.ral_model.get_field_by_name(name);
        field_to_set.set(value);
    endtask

    task update_reg();
        env.ral.ral_model.update(status);
    endtask

    task check_field(string name, uvm_reg_data_t expected_value);
        uvm_reg_field field_to_check;
        field_to_check = env.ral.ral_model.get_field_by_name(name);
        field_to_check.predict(expected_value);
        field_to_check.mirror(status, UVM_CHECK);
    endtask

    task read_field(string name, output uvm_reg_data_t reg_value);
        uvm_reg_field field_to_read;
        field_to_read = env.ral.ral_model.get_field_by_name(name);
        field_to_read.read(status, reg_value);
    endtask

endclass
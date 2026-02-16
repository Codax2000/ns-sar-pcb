import uvm_pkg         ::*;
`include "uvm_macros.svh"

import adc_env_pkg     ::*;
import clkgen_agent_pkg::*;
import input_agent_pkg ::*;
import spi_agent_pkg   ::*;
import reg_env_pkg     ::*;

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
        update_all_reg_burst();

        // mirror values back to make sure they are what we just wrote
        `uvm_info("CONFIG_PHASE", "Reading back registers to make sure write data worked", UVM_MEDIUM);
        mirror_all_reg_burst(UVM_CHECK);

        `uvm_info("CONFIG_PHASE", "Finished Configuring DUT", UVM_MEDIUM)
        
        ral.print();

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

    task update_all_reg();
        env.ral.ral_model.update(status);
    endtask

    task predict_field(string name, uvm_reg_data_t expected_value);
        uvm_reg_field field_to_check;
        field_to_check = env.ral.ral_model.get_field_by_name(name);
        field_to_check.predict(expected_value);
    endtask

    task mirror_field(string name, uvm_reg_data_t expected_value, uvm_check_e check = UVM_NO_CHECK);
        uvm_reg_field field_to_check;
        field_to_check = env.ral.ral_model.get_field_by_name(name);

        if (check == UVM_CHECK)
            field_to_check.predict(expected_value);
    
        field_to_check.mirror(status, check);
    endtask

    task read_field(string name, output uvm_reg_data_t reg_value);
        uvm_reg_field field_to_read;
        field_to_read = env.ral.ral_model.get_field_by_name(name);
        field_to_read.read(status, reg_value);
    endtask

    task write_reg_burst(bit [14:0] address, bit [15:0] write_data [$]);
        uvm_reg                  initial_register;
        spi_packet_reg_extension ext;
        bit [15:0]               address_data;
        uvm_status_e             status;

        initial_register = env.ral.ral_model.default_map.get_reg_by_offset(address);
        ext = spi_packet_reg_extension::type_id::create("burst_write_ext");
        address_data = write_data.pop_front();

        ext.n_additional_reads = 0;
        ext.additional_write_data = write_data;

        initial_register.write(
            .status(status), 
            .value(address_data), 
            .extension(ext)
        );

    endtask

    task mirror_reg_burst(bit [14:0] address, int n_reads, uvm_check_e check = UVM_NO_CHECK);
        uvm_reg                  initial_register;
        spi_packet_reg_extension ext;
        bit [15:0]               address_data;
        uvm_status_e             status;
        bit                      original_check_on_read;
        initial_register = env.ral.ral_model.default_map.get_reg_by_offset(address);
        ext = spi_packet_reg_extension::type_id::create("burst_write_ext");

        ext.n_additional_reads = n_reads - 1;
        ext.additional_write_data = {};

        original_check_on_read = env.ral.ral_model.default_map.get_check_on_read();

        if (check == UVM_CHECK) 
            env.ral.ral_model.default_map.set_check_on_read(1);

        initial_register.mirror(
            .status(status),
            .extension(ext)
        );

        if (check == UVM_CHECK)
            env.ral.ral_model.default_map.set_check_on_read(original_check_on_read);

    endtask

    task mirror_all_reg_burst(uvm_check_e check = UVM_NO_CHECK);
        uvm_reg regs [$];
        int     top_address;
        int     bottom_address;

        env.ral.ral_model.default_map.get_registers(regs);
        bottom_address = regs[0].get_address();
        top_address = bottom_address;

        for (int i = 1; i < regs.size(); i++) begin
            if (regs[i].get_address() > top_address)
                top_address = regs[i].get_address();
        end

        mirror_reg_burst(bottom_address, top_address - bottom_address + 1, check);

    endtask

    task update_all_reg_burst();
        uvm_reg regs [$];
        uvm_reg current_reg;

        bit [14:0]     low_address    ;
        bit [14:0]     high_address   ;
        bit [15:0]     write_data  [$];
        bit            update_data [$];
        uvm_reg_addr_t offset;

        env.ral.ral_model.default_map.get_registers(regs);

        offset = regs[0].get_address();
        low_address = offset;
        high_address = offset;

        for (int i = 1; i < regs.size(); i++) begin
            offset = regs[i].get_address();
            if (offset < low_address)
                low_address = offset;
            if (offset > high_address)
                high_address = offset;
        end

        // starting at low and going to high, get desired value
        write_data.delete();
        update_data.delete();
        for (int i = low_address; i <= high_address; i++) begin
            current_reg = env.ral.ral_model.default_map.get_reg_by_offset(i);
            if (current_reg != null) begin
                if (current_reg.needs_update()) begin
                    write_data.push_back(current_reg.get());
                    update_data.push_back(1);
                end else begin
                    write_data.push_back(current_reg.get_mirrored_value());
                    update_data.push_back(0);
                end
            end else begin
                write_data.push_back(0);
                update_data.push_back(0);
            end
        end

        // trim values that do not need to be updated
        while (update_data[0] == 0) begin
            update_data.pop_front();
            write_data.pop_front();
            low_address++;
        end

        while (update_data[update_data.size() - 1] == 0) begin
            update_data.pop_back();
            write_data.pop_back();
        end

        write_reg_burst(low_address, write_data);

    endtask

endclass

class main_sm_test extends base_test;

    `uvm_component_utils(main_sm_test)

    function new (string name = "main_sm_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function int randomize_config();
        i_env_cfg.randomize() with {
            nfft_power == 4; // NFFT == 16
            osr_power  == 3; // OSR  == 8
            n_sh_total_cycles == 6;
            n_sh_active_cycles == 5;
            n_bottom_plate_active_cycles == 4;
            n_sar_cycles == 1;
            n_int1_total_cycles == 6;
            n_int1_active_cycles == 5;
            n_int2_total_cycles == 6;
            n_int2_active_cycles == 5;
        };
    endfunction

    virtual task main_phase(uvm_phase phase);
        logic readback_status;
        
        phase.raise_objection(this);
        `uvm_info("TEST", "Starting main phase", UVM_MEDIUM)

        write_field("START_CONVERSION", 1);

        do begin
            read_field("START_CONVERSION", readback_status);
        end while (readback_status == 0);

        phase.drop_objection(this);
        `uvm_info("TEST", "Ending main phase", UVM_MEDIUM)
    endtask

endclass
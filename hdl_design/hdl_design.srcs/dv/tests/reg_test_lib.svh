

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
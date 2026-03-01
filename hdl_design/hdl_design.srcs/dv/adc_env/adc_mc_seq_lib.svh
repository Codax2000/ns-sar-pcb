class reset_seq extends uvm_sequence;

    `uvm_object_utils(reset_seq)
    `uvm_declare_p_sequencer(adc_mc_sequencer)
    
    string field_name;

    function new(string name = "reset_seq");
        super.new(name);
        field_name = "SYNC_RESET_RB";
    endfunction

    rand int reset_duration_ns;

    constraint legal_reset_duration {
        reset_duration_ns >= 100;
        reset_duration_ns <= 10000; // 100 ns to 10us
    }

    virtual task body();
        uvm_reg_data_t               value;
        uvm_status_e                 status;

        p_sequencer.reset_seq.randomize() with {
            seq_value == 1;
        };
        p_sequencer.adc_seq.randomize() with {
            pkt_enabled == 0;
        };

        fork
            p_sequencer.reset_seq.start(p_sequencer.m_reset_sequencer);
            p_sequencer.adc_seq.start(p_sequencer.m_adc_in_sequencer);
        join

        #(reset_duration_ns);
        p_sequencer.reset_seq.randomize() with {
            seq_value == 0;
        };
        p_sequencer.reset_seq.start(p_sequencer.m_reset_sequencer);
        
        p_sequencer.ral.get_field_by_name(field_name).read(status, value);
        if (value != 1)
            `uvm_error(get_full_name(), "Expected synchronous reset readback to be 1, received 0 (no readback, device still in reset)")
        else
            `uvm_info(get_full_name(), "Expected synchronous reset readback to be 1, received 1", UVM_LOW)
    endtask

endclass
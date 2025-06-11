class single_const_value_conversion_seq extends uvm_sequence;

    `uvm_object_utils(single_const_value_conversion_seq)
    `uvm_declare_p_sequencer(adc_mc_sequencer)

    set_random_value_seq srv_seq;
    uvm_status_e status;
    uvm_reg_data_t fsm_status_rb;

    rand int nfft;

    constraint legal_nfft {
        nfft > 0;
        nfft <= 1 << 15;
    }

    function new(string name = "single_const_value_conversion_seq");
        super.new(name);
    endfunction

    task body();
        for (int i = 0; i < nfft; i++) begin
            srv_seq = set_random_value_seq::type_id::create("srv_seq");
            srv_seq.start(p_sequencer.input_sequencer);
            p_sequencer.ral.ral_model.get_field_by_name("begin_sample").write(status, 1);
            do begin
                `uvm_info("MC_SEQR", "Waiting for conversion to end", UVM_MEDIUM);
                p_sequencer.ral.ral_model.get_field_by_name("begin_sample").read(status, fsm_status_rb);
            end while (fsm_status_rb != 0);
            p_sequencer.ral.ral_model.get_field_by_name("read_mem").write(status, 1);
        end
    endtask

endclass
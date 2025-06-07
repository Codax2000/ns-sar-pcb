class set_random_value_seq extends uvm_sequence #(const_packet);

    `uvm_object_utils(set_random_value_seq)

    function new(string name = "drive_random_value_seq");
        super.new(name);
    endfunction

    virtual task body();
        const_packet item;
        `uvm_info("SEQ", "Driving random value", UVM_LOW)

        item = const_packet::type_id::create("item");
        start_item(item);
        assert (item.randomize());
        finish_item(item);
        `uvm_info("SEQ", "Sine wave amplitude changed and frequency set to 0", UVM_LOW)

    endtask

endclass

class drive_sine_wave_seq extends uvm_sequence #(sin_packet);

    int nfft;
    int osr;
    real fs;
    sin_packet item;

    `uvm_object_utils(drive_sine_wave_seq)
    `uvm_declare_p_sequencer(uvm_sequencer #(sin_packet))

    function new(string name = "drive_sine_wave");
        super.new(name);
    endfunction

    virtual task body();
        `uvm_info("SEQ", "Driving Sine wave", UVM_LOW)
        if (!uvm_config_db #(int) :: get(p_sequencer, "", "nfft", nfft))
            `uvm_fatal("SEQ", "Could not attach NFFT")
        if (!uvm_config_db #(int) :: get(p_sequencer, "", "osr", osr))
            `uvm_fatal("SEQ", "Could not attach OSR")
        if (!uvm_config_db #(real) :: get(p_sequencer, "", "fs", fs))
            `uvm_fatal("SEQ", "Could not attach sampling frequency")

        item = sin_packet::type_id::create("pkt");
        item.set_nfft(nfft);
        item.set_osr(osr);
        item.set_fs(fs);
        item.randomize();

        start_item(item);
        finish_item(item);

        `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)

    endtask

endclass
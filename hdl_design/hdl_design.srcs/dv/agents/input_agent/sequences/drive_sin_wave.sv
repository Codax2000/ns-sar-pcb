class drive_sine_wave extends uvm_sequence #(sin_packet);

    int nfft;
    sin_packet item;

    `uvm_object_utils(drive_sine_wave)

    function new(string name = "drive_sine_wave");
        super.new(name);
        if (!uvm_config_db #(int) :: get(null, "*", "nfft", nfft))
            `uvm_fatal("SEQ", "NFFT not found")
    endfunction

    virtual task body();
        `uvm_info("SEQ", "Driving Sine wave", UVM_LOW)
        item = sin_packet::type_id::create("pkt");
        item.set_nfft(nfft);
        start_item(item);
        assert (item.randomize());
        item.print();
        finish_item(item);

        `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)

    endtask

endclass
class drive_sine_wave extends uvm_sequence #(sin_packet);

    int nfft;

    `uvm_object_utils(drive_sine_wave)

    function new(string name = "drive_sine_wave");
        super.new(name);
        this.nfft = 32;
    endfunction

    virtual task body();
        sin_packet item;
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
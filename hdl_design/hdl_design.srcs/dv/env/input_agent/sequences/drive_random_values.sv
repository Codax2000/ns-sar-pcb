class drive_sine_wave extends uvm_sequence #(sin_packet);
    `uvm_object_utils(drive_sine_wave)

    int n_samples;

    function new(string name = "drive_sine_wave", int nfft);
        super.new(name);
        n_samples = nfft;
    endfunction

    virtual task body();
        sin_packet item;
        `uvm_info("SEQ", "Driving random values", UVM_LOW)

        repeat (n_samples) begin
            item = sin_packet::type_id::create("item");
            start_item(item);
            assert (item.randomize());
            finish_item(item);
        end

        `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)

    endtask

endclass
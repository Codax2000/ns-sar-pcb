class drive_random_values extends uvm_sequence #(sin_packet);
    `uvm_object_utils(drive_random_values)

    int n_samples;

    function new(string name = "drive_random_values");
        super.new(name);
        if (!uvm_config_db #(int) :: get(null, "*", "nfft", n_samples))
            `uvm_fatal("SEQ", "NFFT not found")
    endfunction

    virtual task body();
        sin_packet item;
        `uvm_info("SEQ", "Driving random values", UVM_LOW)

        repeat (n_samples) begin
            item = sin_packet::type_id::create("item");
            item.set_nfft(n_samples);
            start_item(item);
            assert (item.randomize());
            finish_item(item);
            `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)
        end


    endtask

endclass
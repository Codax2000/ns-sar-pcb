import uvm_pkg::*;

class drive_random_values extends uvm_sequence #(sin_packet);
    `uvm_object_utils(drive_sine_wave)

    int n_samples;

    function new(string name = "drive_random_values");
        super.new(name);
        if (!uvm_config_db#(int)::get(this, "", "nfft", n_samples))
            `uvm_fatal("CONFIG", "NFFT not found", UVM_LOW)
    endfunction

    virtual task body();
        sin_packet item;
        `uvm_info("SEQ", "Driving random values", UVM_LOW)

        repeat (n_samples) begin
            item = sin_packet::type_id::create("item");
            start_item(item);
            assert (item.randomize());
            finish_item(item);
            `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)
        end


    endtask

endclass
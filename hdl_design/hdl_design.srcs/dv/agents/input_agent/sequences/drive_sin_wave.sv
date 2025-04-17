import uvm_pkg::*;

class drive_sine_wave extends uvm_sequence #(sin_packet);
    `uvm_object_utils(drive_sine_wave)

    function new(string name = "drive_sine_wave");
        super.new(name);
    endfunction

    virtual task body();
        sin_packet item;
        `uvm_info("SEQ", "Driving Sine wave", UVM_LOW)

        item = sin_packet::type_id::create("item");
        start_item(item);
        assert (item.randomize());
        finish_item(item);

        `uvm_info("SEQ", "Sine wave frequency and amplitude changed", UVM_LOW)

    endtask

endclass
/**
Class: single_value_seq

Sequence with a single random value. Can be randomized or set, and the packet will take on
the same value if legal. The nice thing is that this means values can potentially be constrained
here instead of the packet class.
*/
class single_value_seq #(int WIDTH = 1) extends uvm_sequence #(bit_bus_packet #(.WIDTH(WIDTH)));

    `uvm_object_param_utils(single_value_seq #(WIDTH))

    function new (string name = "single_value_seq");
        super.new(name);
    endfunction

    rand bit [WIDTH-1:0] seq_value;

    bit_bus_packet #(.WIDTH(WIDTH)) pkt;

    virtual task body();
        pkt = bit_bus_packet #(.WIDTH(WIDTH))::type_id::create("pkt");

        `uvm_info(get_full_name(), $sformatf("Single-value sequence: %b", value), UVM_HIGH)

        `uvm_do_with(pkt, { value == seq_value })

    endtask

endclass
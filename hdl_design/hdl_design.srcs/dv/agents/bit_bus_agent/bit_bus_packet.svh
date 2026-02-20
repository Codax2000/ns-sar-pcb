/**
 * Class: bit_bus_packet
 *
 * Generic N‑bit transaction.
 * Contains a randomized vector that will be driven onto the DUT.
 */
class bit_bus_packet #(int WIDTH = 1) extends uvm_sequence_item;

    rand bit [WIDTH-1:0] value;

    `uvm_object_param_utils_begin(bit_bus_packet #(WIDTH))
        `uvm_field_int(value, UVM_ALL_ON)
    `uvm_object_param_utils_end

    function new(string name = "bit_bus_packet");
        super.new(name);
        `uvm_info("BIT_BUS_PKT",
                  $sformatf("bit_bus_packet created (WIDTH=%0d)", WIDTH),
                  UVM_LOW)
    endfunction

endclass
/**
Class: spi_packet_reg_extension

Utility class for passing to the adapter for specifying burst reads or writes.
Can be passed as the extension argument when calling uvm_reg::read, write, update, and
the same fields for uvm_reg_field.

Extended read would be done by passing empty data; the size of the array is the
great thing in that scenario.
*/
class spi_packet_reg_extension extends uvm_object;

    `uvm_object_utils(spi_packet_reg_extension)

    rand logic [15:0] additional_write_data [$];

    function new(string name = "spi_packet_reg_extension");
        super.new(name);
    endfunction

endclass
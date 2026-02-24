/**
Class: spi_packet_reg_extension

Utility class for passing to the adapter for specifying burst reads or writes.
Can be passed as the extension argument when calling uvm_reg::read, write, update, and
the same fields for uvm_reg_field.
*/
class spi_packet_reg_extension extends uvm_object;

    `uvm_object_utils(spi_packet_reg_extension)

    rand logic [7:0] additional_write_data [$];
    rand int         n_additional_reads;

    function new(string name = "spi_packet_reg_extension");
        super.new(name);
    endfunction

endclass
import uvm_pkg::*;
`include "uvm_macros.svh"

class spi_packet extends uvm_sequence_item;

    // relevant data for DUT
    rand logic        rd_en;
    rand logic [14:0] address;
    rand logic [15:0] write_data [$];
         logic [15:0] read_data [$]; // data out - monitor publishes multiple transactions
    
    // data for driver/monitor
    rand int        n_reads;
         bit        is_subsequent_transaction;

    constraint no_write_data_if_read {
        rd_en -> (write_data.size() == 0);
    }

    constraint short_reads {
        n_reads < 10;
        n_reads >= 0;
        if (rd_en) {
            n_reads > 0;
        }
        else {
            n_reads == 0;
        }
    }

    `uvm_object_utils_begin(spi_packet)
        `uvm_field_int(rd_en, UVM_ALL_ON)
        `uvm_field_int(address, UVM_ALL_ON)
        `uvm_field_queue_int(write_data, UVM_ALL_ON)
        `uvm_field_int(n_reads, UVM_ALL_ON)
        `uvm_field_queue_int(read_data, UVM_ALL_ON)
        `uvm_field_int(is_subsequent_transaction, UVM_ALL_ON)
    `uvm_object_utils_end

    function new (string name = "spi_packet");
        super.new(name);
        `uvm_info("PKT", "SPI packet created", "UVM_LOW")
    endfunction

endclass
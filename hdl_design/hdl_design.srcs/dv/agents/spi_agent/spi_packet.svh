/**
Class: spi_packet

Sequence item defining a SPI transaction. Transactions can be either a single-byte
read/write or a burst read/write.
*/
class spi_packet extends uvm_sequence_item;

    // relevant data for DUT
    rand logic        rd_en;
    rand spi_parity_t header_parity;

    rand logic [15:0] address;
    rand spi_parity_t address_parity [2];

    rand logic [7:0]  write_data   [$];
    rand spi_parity_t write_parity [$];

    // data for driver/monitor
    rand int          n_reads;
    rand spi_parity_t read_parity [$];
         logic [7:0]  read_data   [$]; // data out - monitor publishes multiple transactions

         bit        is_subsequent_transaction;

    constraint no_write_data_if_read {
        if (rd_en) {
            write_data.size() == 0;
            write_parity.size() == 0;
            read_parity.size() == n_reads;
        } else {
            write_data.size() == write_parity.size();
        }
    }

    constraint all_good_parity_soft {
        soft header_parity == GOOD_PARITY;
        foreach (address_parity[i]) {
            soft address_parity[i] == GOOD_PARITY;
        }
        foreach (write_parity[i]) {
            soft write_parity[i] == GOOD_PARITY;
        }
        foreach (read_parity[i]) {
            soft read_parity[i] == GOOD_PARITY;
        }
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
        `uvm_field_queue_int(write_parity, UVM_ALL_ON)
        `uvm_field_int(n_reads, UVM_ALL_ON)
        `uvm_field_queue_int(read_data, UVM_ALL_ON)
        `uvm_field_int(is_subsequent_transaction, UVM_ALL_ON)
    `uvm_object_utils_end

    function new (string name = "spi_packet");
        super.new(name);
        `uvm_info("PKT", "SPI packet created", "UVM_LOW")
    endfunction

endclass
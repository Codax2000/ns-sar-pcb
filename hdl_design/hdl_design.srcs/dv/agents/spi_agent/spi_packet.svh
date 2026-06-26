/*
Class: spi_packet

Sequence item defining a SPI transaction. Transactions are modeled as
symmetric queues of MISO and MOSI byte data.

*/
class spi_packet extends uvm_sequence_item;

    /*
    Variable: mosi
    Queue of bytes representing Master Out Slave In data payload.
    */
    rand logic [7:0] mosi [$];

    /*
    Variable: miso
    Queue of bytes representing Master In Slave Out data payload.
    */
         logic [7:0] miso [$];
    
    /*
    Variable: transfer_size
    The total number of bytes to be transferred during this SPI transaction.
    */
    rand int unsigned transfer_size;

    `uvm_object_utils_begin(spi_packet)
        `uvm_field_queue_int(mosi,          UVM_DEFAULT)
        `uvm_field_queue_int(miso,          UVM_DEFAULT)
        `uvm_field_int      (transfer_size, UVM_DEFAULT)
    `uvm_object_utils_end

    /*
    Constraint: c_transfer_size
    
    Limits the <transfer_size> to a reasonable simulation range (1 to 64 bytes) 
    and forces both <mosi> and <miso> queues to match this length.
    */
    constraint c_transfer_size {
        transfer_size inside {[1:64]}; 
        mosi.size() == transfer_size;
    }

    function new(string name = "spi_packet");
        super.new(name);
    endfunction : new

endclass : spi_packet
class spi_packet_wrapper extends uvm_sequence #(spi_packet);

    spi_packet item;

    `uvm_object_utils(spi_packet_wrapper)

    function new(string name = "spi_packet_wrapper");
        super.new(name);
    endfunction

    virtual task body();
        `uvm_info("SEQ", "Sending SPI Packet", UVM_LOW)
        item = spi_packet::type_id::create("pkt");
        start_item(item);
        assert (item.randomize());
        item.print();
        finish_item(item);

        `uvm_info("SEQ", "SPI Packet Sent", UVM_LOW)

    endtask

endclass
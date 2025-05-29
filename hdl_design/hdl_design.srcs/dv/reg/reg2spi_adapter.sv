class reg2spi_adapter extends uvm_reg_adapter;

    `uvm_object_utils(reg2spi_adapter)

    function new (string name = "reg2spi_adapter");
        super.new(name);
        supports_byte_enable = 0;
        provides_responses = 0;
    endfunction

    virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
        spi_packet pkt = spi_pkt::type_id::create("pkt");
        pkt.reg_index = rw.addr;
        pkt.mosi_data = rw.data;
        pkt.command = rw.kind == READ   ? 2'b00 :
                      rw.addr <= 2      ? 2'b01 :
                      rw.data[2]        ? 2'b10 : 
                      rw.data[3]        ? 2'b11;
        `uvm_info ("adapter",
                   $sformatf ("reg2bus addr=0x%0h data=0x%0h kind=%s",
                              pkt.addr, pkt.data, rw.kind.name),
                   UVM_DEBUG)
        return pkt;
    endfunction

    virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
        spi_packet pkt;

        if (! $cast (pkt, bus_item))
            `uvm_fatal("reg2spi_adapter", "Failed to cast bus item to SPI packet");
        
        rw.kind = pkt.command == 2'b00 ? READ : WRITE ;
        rw.addr = (pkt.command == 2'b10 || pkt.command == 2'b11) ? 2'h3 : pkt.reg_index;
        rw.data = (pkt.command == 2'b10 || pkt.command == 2'b11) ? 4'h0 : pkt.reg_response;
        rw.status = UVM_IS_OK;

        `uvm_info ("adapter", $sformatf("bus2reg : addr=0x%0h data=0x%0h kind=%s status=%s", rw.addr, rw.data, rw.kind.name(), rw.status.name()), UVM_DEBUG)
   
    endfunction

endclass
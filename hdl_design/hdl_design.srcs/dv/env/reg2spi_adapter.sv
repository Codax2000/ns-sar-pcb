import spi_agent_pkg::*;

class reg2spi_adapter extends uvm_reg_adapter;

    `uvm_object_utils(reg2spi_adapter)

    function new (string name = "reg2spi_adapter");
        super.new(name);
        supports_byte_enable = 0;
        provides_responses = 0;
    endfunction

    virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
        spi_packet pkt;
        
        pkt = spi_packet::type_id::create("pkt");
        pkt.rd_en = rw.kind == UVM_READ;
        pkt.address = rw.addr;
        pkt.n_reads = rw.kind == UVM_READ ? 1 : 0;
        pkt.write_data.delete();
        pkt.read_data.delete();
        if (rw.kind == UVM_WRITE)
            pkt.write_data.push_back(rw.data);
            
        
        `uvm_info ("adapter",
                   $sformatf ("reg2bus addr=0x%0h data=0x%0h kind=%s",
                              rw.addr, rw.data, rw.kind.name()),
                   UVM_MEDIUM)
        return pkt;
    endfunction

    virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
        spi_packet pkt;

        if (! $cast (pkt, bus_item))
            `uvm_fatal("reg2spi_adapter", "Failed to cast bus item to SPI packet");
            
        rw.kind = pkt.rd_en ? UVM_READ : UVM_WRITE ;
        rw.addr = pkt.address;
        rw.data = pkt.rd_en ? pkt.read_data[0] : pkt.write_data[0];
        rw.status = UVM_IS_OK;

        `uvm_info ("adapter", 
                   $sformatf("bus2reg : addr=0x%0h data=0x%0h kind=%s status=%s",
                             rw.addr, rw.data, rw.kind.name(), rw.status.name()),
                   UVM_MEDIUM)
        pkt.print();
    endfunction

endclass
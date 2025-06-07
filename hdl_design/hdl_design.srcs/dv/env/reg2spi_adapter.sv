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
        pkt.reg_index = rw.addr;
        pkt.mosi_data = rw.data;
        pkt.command = rw.kind == UVM_READ   ? 2'b00 :
                      rw.addr <= 2      ? 2'b01 :
                      rw.data[2]        ? 2'b10 : 2'b11;
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
            
        rw.kind = pkt.command == 2'b00 ? UVM_READ : UVM_WRITE ;
        rw.addr = (pkt.command == 2'b10 || pkt.command == 2'b11) ? 2'h3 : pkt.reg_index;
        rw.data = (pkt.command == 2'b10) ? 4'h4 :
                  (pkt.command == 2'b11) ? 4'h8 : pkt.reg_response;
        rw.status = UVM_IS_OK;

        `uvm_info ("adapter", 
                   $sformatf("bus2reg : addr=0x%0h data=0x%0h kind=%s status=%s",
                             rw.addr, rw.data, rw.kind.name(), rw.status.name()),
                   UVM_MEDIUM)
   
    endfunction

endclass
/**
Class: reg2spi_adapter

SPI-specific adapter that translates SPI packets into generic uvm_reg_bus_op
items. Supports byte lane enables.
*/
class reg2spi_adapter extends uvm_reg_adapter;

    `uvm_object_utils(reg2spi_adapter)

    function new (string name = "reg2spi_adapter");
        super.new(name);
        supports_byte_enable = 1;
        provides_responses = 0;
    endfunction

    virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
        spi_packet               pkt;
        uvm_reg_item             item;
        spi_packet_reg_extension ext;
        int i = 0;

        item = get_item();
        pkt = spi_packet::type_id::create("driver_spi_pkt");
        ext = spi_packet_reg_extension::type_id::create("ext");

        pkt.rd_en = rw.kind == UVM_READ;
        pkt.address = rw.addr;
        pkt.address_parity[0] = GOOD_PARITY;
        pkt.address_parity[1] = GOOD_PARITY;
        pkt.header_parity     = GOOD_PARITY;

        pkt.is_subsequent_transaction = 0;

        // deal with data
        if (pkt.rd_en) begin
            pkt.write_data.delete();
            pkt.write_parity.delete();
            case (rw.byte_en[1:0])
                0 : `uvm_fatal(get_full_name(), "Received a packet with no enabled byte lanes.")
                1 : begin
                    pkt.n_reads = 1;
                    pkt.read_parity.push_back(GOOD_PARITY);
                end
                2 : begin
                    pkt.n_reads = 1;
                    pkt.address++;
                    pkt.read_parity.push_back(GOOD_PARITY);
                end
                3 : begin
                    pkt.n_reads = 2;
                    pkt.read_parity.push_back(GOOD_PARITY);
                    pkt.read_parity.push_back(GOOD_PARITY);
                end
            endcase
        end
        else begin
            pkt.n_reads = 0;
            pkt.read_parity.delete();
            case (rw.byte_en[1:0])
                0 : `uvm_fatal(get_full_name(), "Received a packet with no enabled byte lanes.")
                1 : begin
                    pkt.write_data.push_back(rw.data[7:0]);
                    pkt.write_parity.push_back(GOOD_PARITY);
                end
                2 : begin
                    pkt.address++;
                    pkt.write_data.push_back(rw.data[15:8]);
                    pkt.write_parity.push_back(GOOD_PARITY);
                end
                3 : begin
                    pkt.write_data.push_back(rw.data[7:0]);
                    pkt.write_data.push_back(rw.data[15:8]);
                    pkt.write_parity.push_back(GOOD_PARITY);
                    pkt.write_parity.push_back(GOOD_PARITY);
                end
            endcase
        end

        
        if (item.extension != null) begin
            if (! $cast(ext, item.extension))
                `uvm_fatal("ADAPTER", "Failed to cast item extension to SPI packet extension")
            if (rw.kind == UVM_WRITE) begin
                while (ext.additional_write_data.size() > 0) begin
                    pkt.write_data.push_back(ext.additional_write_data[0]);
                    pkt.write_parity.push_back(GOOD_PARITY);
                    ext.additional_write_data.pop_front();
                end
            end
            if (rw.kind == UVM_READ) begin
                for (int i = 0; i < ext.n_additional_reads; i++) begin
                    pkt.n_reads++;
                    pkt.read_parity.push_back(GOOD_PARITY);
                end
            end
        end
        
        `uvm_info ("ADAPTER",
                   $sformatf ("reg2bus addr=0x%0h data=0x%0h kind=%s byte_en=%h",
                              rw.addr, rw.data, rw.kind.name(), rw.byte_en),
                   UVM_MEDIUM)
        return pkt;
    endfunction

    virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
        spi_packet   pkt;
        spi_parity_t header_parity;
        spi_parity_t resolved_parity;

        if (! $cast (pkt, bus_item))
            `uvm_fatal("reg2spi_adapter", "Failed to cast bus item to SPI packet");
            
        rw.kind = pkt.rd_en ? UVM_READ : UVM_WRITE ;
        rw.addr = pkt.address[15:1];
        rw.byte_en = 1 << pkt.address[0];
        rw.data = pkt.rd_en ? pkt.read_data[0] : pkt.write_data[0];

        header_parity = (pkt.header_parity == GOOD_PARITY) &&
                        (pkt.address_parity[0] == GOOD_PARITY) &&
                        (pkt.address_parity[1] == GOOD_PARITY) ? GOOD_PARITY : BAD_PARITY;
        resolved_parity = pkt.rd_en ?
                              (header_parity == GOOD_PARITY) && (pkt.read_parity[0] == GOOD_PARITY) ?
                                  GOOD_PARITY :
                                  BAD_PARITY : // else if write packet,
                              (header_parity == GOOD_PARITY) && (pkt.write_parity[0] == GOOD_PARITY) ?
                                  GOOD_PARITY :
                                  BAD_PARITY;
        rw.status = resolved_parity == GOOD_PARITY ? UVM_IS_OK : UVM_NOT_OK;

        `uvm_info ("ADAPTER", 
                   $sformatf("bus2reg : addr=0x%0h data=0x%0h kind=%s byte_en=%h status=%s",
                             rw.addr, rw.data, rw.kind.name(), rw.byte_en, rw.status.name()),
                   UVM_MEDIUM)
        pkt.print();
    endfunction

endclass
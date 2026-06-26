/**
Class: reg2spi_adapter

SPI-specific adapter that translates SPI packets into generic uvm_reg_bus_op
items. Supports byte lane enables.
*/
class reg2spi_adapter extends uvm_reg_adapter;

    `uvm_object_utils(reg2spi_adapter)

    function new (string name = "reg2spi_adapter");
        super.new(name);
        supports_byte_enable = 0;
        provides_responses = 0;
    endfunction

    virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
        spi_packet               pkt;
        uvm_reg_item             item;
        spi_packet_reg_extension ext;
        logic [15:0]             write_byte;

        item = get_item();
        pkt = spi_packet::type_id::create("driver_spi_pkt");
        ext = spi_packet_reg_extension::type_id::create("ext");

        write_byte[15]   = rw.kind == UVM_READ;
        write_byte[14:0] = rw.addr;
        pkt.mosi.push_back(write_byte[15:8]);
        pkt.mosi.push_back(write_byte[7:0]);

        // deal with data
        if (pkt.rd_en) begin
            std::randomize(write_byte);
            pkt.mosi.push_back(write_byte[15:8]);
            pkt.mosi.push_back(write_byte[7:0]);
        end
        else begin
            pkt.mosi.push_back(item.value[15:8]);
            pkt.mosi.push_back(item.value[7:0]);
        end

        
        if (item.extension != null) begin
            if (! $cast(ext, item.extension))
                `uvm_fatal("ADAPTER", "Failed to cast item extension to SPI packet extension")
            while (ext.additional_write_data.size() > 0) begin
                write_byte = ext.additional_write_data.pop();
                pkt.mosi.push_back(write_byte[15:8]);
                pkt.mosi.push_back(write_byte[7:0]);
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

        if (! $cast (pkt, bus_item))
            `uvm_fatal("reg2spi_adapter", "Failed to cast bus item to SPI packet");
            
        rw.kind = pkt.rd_en ? UVM_READ : UVM_WRITE ;
        rw.addr = {pkt.address[15:1], 1'b0};
        rw.data = pkt.rd_en ? pkt.read_data[0] : pkt.write_data[0];

        rw.status = resolved_parity == GOOD_PARITY ? UVM_IS_OK : UVM_NOT_OK;

        if (pkt.mosi.size() != pkt.miso.size() || pkt.mosi.size() < 4)
            rw.status = UVM_NOT_OK;
        else begin
            rw.kind = pkt.mosi[0][7] ? UVM_READ : UVM_WRITE;
            rw.addr = 15'{pkt.mosi[0][6:0], pkt.mosi[1]};

            if (rw.kind == UVM_WRITE)
                rw.data = 16'{pkt.mosi[2], pkt.mosi[3]};
            else
                rw.data = 16'{pkt.miso[2], pkt.miso[3]};
        end
        
        `uvm_info ("ADAPTER", 
                   $sformatf("bus2reg : addr=0x%0h data=0x%0h kind=%s byte_en=%h status=%s",
                             rw.addr, rw.data, rw.kind.name(), rw.byte_en, rw.status.name()),
                   UVM_MEDIUM)
        `uvm_info(get_full_name(), $sformatf("Current Packet:\n%s", pkt.sprint()), UVM_HIGH);
    endfunction

endclass
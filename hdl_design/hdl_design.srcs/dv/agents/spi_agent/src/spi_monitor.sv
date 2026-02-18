class spi_monitor extends uvm_monitor;

    `uvm_component_utils(spi_monitor)

    virtual if_spi vif;
    uvm_analysis_port #(spi_packet) mon_analysis_port;

    bit CPOL;
    bit CPHA;

    logic [15:0] read_data_queue [$];

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_spi)::get(this, "", "vif", vif))
            `uvm_fatal("MON", "Virtual interface not found for SPI Monitor")
        if (!uvm_config_db #(bit)::get(this, "", "CPOL", CPOL))
            `uvm_fatal("MON", "Could not attach monitor CPOL")
        if (!uvm_config_db #(bit)::get(this, "", "CPHA", CPHA))
            `uvm_fatal("MON", "Could not attach monitor CPHA")
    endfunction

    virtual task run_phase(uvm_phase phase);
        spi_packet item;
        forever begin
            item = spi_packet::type_id::create("mon_packet");
            collect_transaction(item);
        end
    endtask

    virtual task collect_transaction(spi_packet item);
        @(negedge vif.csb);
        `uvm_info("MON", "Collecting SPI Packet", UVM_HIGH)
        collect_signals(item);
    endtask

    virtual task collect_signals(spi_packet item);
        logic [15:0] reg_temp;
        spi_packet copy_pkt = spi_packet::type_id::create("monitor_spi_pkt_copy");

        item.read_data.delete();
        item.write_data.delete();
        
        // collect transaction type
        @(posedge vif.scl);
        item.rd_en = vif.mosi;
        
        // collect address
        for (int i = 14; (i >= 0) && (!vif.csb); i--) begin
            @(posedge vif.scl or posedge vif.csb);
            item.address[i] = vif.mosi;
        end

        // receive MISO data if read, MOSI if write
        if (item.rd_en) begin : reg_read
            while (!vif.csb) begin
                // monitor transaction
                reg_temp = 16'h0000;
                for (int j = 15; (j >= 0) && (!vif.csb); j--) begin
                    @(posedge vif.scl or posedge vif.csb);
                    reg_temp[j] = vif.miso;
                end
                if (!vif.csb) begin
                    item.n_reads++;
                    item.read_data.push_back(reg_temp);
                end

                // publish transaction
                copy_pkt.copy(item);
                copy_pkt.read_data.delete();
                copy_pkt.read_data.push_back(reg_temp);
                copy_pkt.address += (copy_pkt.n_reads - 1);
                copy_pkt.is_subsequent_transaction = item.n_reads > 1;
                if (!vif.csb) begin
                    `uvm_info("MON", "Sending Read Packet", UVM_HIGH)
                    mon_analysis_port.write(copy_pkt);
                end
            end
        end else begin : reg_write
            while (!vif.csb) begin
                reg_temp = 16'h0000;
                for (int j = 15; (j >= 0) && (!vif.csb); j--) begin
                    @(posedge vif.scl or posedge vif.csb);
                    reg_temp[j] = vif.mosi;
                end
                if (!vif.csb)
                    item.write_data.push_back(reg_temp);

                // publish transaction
                copy_pkt.copy(item);
                copy_pkt.write_data.delete();
                copy_pkt.write_data.push_back(reg_temp);
                copy_pkt.address += (item.write_data.size() - 1);
                copy_pkt.is_subsequent_transaction = copy_pkt.address != item.address;
                if (!vif.csb) begin
                    `uvm_info("MON", "Sending Write Packet", UVM_HIGH)
                    mon_analysis_port.write(copy_pkt);
                end
            end
        end

    endtask
endclass
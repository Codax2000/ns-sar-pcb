/**
Class: spi_monitor

Monitors the SPI bus for transactions and publishes them. Note: this monitor
publishes entire transactions. That means if a transaction is a burst, it publishes a single
burst transaction, which will not be RAL-compatible and so should be interdicted by an
instance of <spi_packet_splitter> before being sent to the RAL predictor.

Additionally, if a transaction terminates before having 8 bits in a read/write packet,
that packet is published anyway with Xs.
*/
class spi_monitor extends uvm_monitor;

    `uvm_component_utils(spi_monitor)

    virtual spi_if vif;
    uvm_analysis_port #(spi_packet) mon_analysis_port;

    bit CPOL;
    bit CPHA;

    logic [15:0] read_data_queue [$];

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual spi_if)::get(this, "", "vif", vif))
            `uvm_fatal("MON", "Virtual interface not found for SPI Monitor")
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
        logic [7:0] reg_temp;

        item = spi_packet::type_id::create("monitor_spi_pkt_copy");
        item.is_subsequent_transaction = 0;
        
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
                reg_temp = 8'bxxxx_xxxx;
                for (int j = 7; (j >= 0) && (!vif.csb); j--) begin
                    @(posedge vif.scl or posedge vif.csb);
                    reg_temp[j] = vif.miso;
                end
                item.n_reads++;
                item.read_data.push_back(reg_temp);
            end
            
            `uvm_info("MON", $sformatf("Sending Read Packet", item.sprint()), UVM_HIGH)
            mon_analysis_port.write(item);
        end else begin : reg_write
            while (!vif.csb) begin
                reg_temp = 8'bxxxx_xxxx;
                for (int j = 7; (j >= 0) && (!vif.csb); j--) begin
                    @(posedge vif.scl or posedge vif.csb);
                    reg_temp[j] = vif.mosi;
                end
                item.write_data.push_back(reg_temp);
            end

            `uvm_info("MON", $sformatf("Sending Write Packet", item.sprint()), UVM_HIGH)
            mon_analysis_port.write(item);
        end

    endtask
endclass
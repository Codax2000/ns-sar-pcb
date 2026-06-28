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
            @(negedge vif.csb);
            item = spi_packet::type_id::create("mon_packet");
            collect_transaction(item);
            `uvm_info(get_full_name(), $sformatf("Collected monitor packet: %s", item.sprint()), UVM_HIGH)
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(spi_packet item);
        int bit_counter;
        logic [7:0] mosi_byte;
        logic [7:0] miso_byte;

        bit_counter = 7;

        while (!vif.csb) begin
            @(posedge vif.scl or posedge vif.csb);
            if (!vif.csb)
                mosi_byte[bit_counter] = vif.mosi;
            @(negedge vif.scl or posedge vif.csb);
            if (!vif.csb)
                miso_byte[bit_counter] = vif.miso;
            if (bit_counter == 0) begin
                bit_counter = 7;
                item.mosi.push_back(mosi_byte);
                item.miso.push_back(miso_byte);
            end
            else
                bit_counter--;
        end
    endtask

endclass
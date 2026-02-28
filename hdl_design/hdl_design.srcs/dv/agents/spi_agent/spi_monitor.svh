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
            @(negedge vif.csb);
            item = spi_packet::type_id::create("mon_packet");
            collect_transaction(item);
            `uvm_info(get_full_name(), $sformatf("Collected monitor packet: %s", item.sprint()), UVM_MEDIUM)
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(spi_packet item);
        logic [7:0] current_byte;
        spi_parity_t current_parity;
        int n_observed_transactions;
        int n_expected_transactions;

        n_observed_transactions = 0;
        n_expected_transactions = 0;

        observe_byte(1, current_byte, current_parity);
        item.rd_en = current_byte[0];
        n_expected_transactions = current_byte[7:1] + 1;
        item.header_parity = current_parity;

        observe_byte(1, item.address[7:0], item.address_parity[0]);
        observe_byte(1, item.address[15:8], item.address_parity[1]);
        `uvm_info(get_full_name(),
                  $sformatf("Observed SPI address=%h, rd_en=%b, %0d expected transaction bytes", 
                            item.address, item.rd_en, n_expected_transactions),
                  UVM_MEDIUM)
        while (n_observed_transactions != n_expected_transactions) begin
            `uvm_info(get_full_name(), $sformatf("Observing SPI data"), UVM_MEDIUM)
            observe_byte(!item.rd_en, current_byte, current_parity);
            n_observed_transactions++;
            
            if (item.rd_en) begin
                item.read_data.push_back(current_byte);
                item.read_parity.push_back(current_parity);
                item.n_reads++;
            end else begin
                item.write_data.push_back(current_byte);
                item.write_parity.push_back(current_parity);
            end

        end
        @(posedge vif.csb);

    endtask

    virtual task observe_byte(bit watch_mosi,
                              output logic [7:0] current_byte,
                              output spi_parity_t current_parity);
        bit parity_count;
        
        parity_count = 1;
        current_byte = 8'bxxxx_xxxx;
        current_parity = BAD_PARITY;

        for (int i = 0; i < 8; i++) begin
            @(posedge vif.scl);
            current_byte[i] = watch_mosi ? vif.mosi : vif.miso;
            parity_count = parity_count ^ current_byte[i];
        end
        // wait another clock cycle and check parity
        @(posedge vif.scl);
        if ((parity_count == vif.mosi) && (parity_count == vif.miso))
            current_parity = GOOD_PARITY;
        
        `uvm_info(get_full_name(),
                  $sformatf("Observed monitor byte: data=%h, parity=%s",
                            current_byte, current_parity.name()),
                  UVM_MEDIUM)
    endtask

endclass
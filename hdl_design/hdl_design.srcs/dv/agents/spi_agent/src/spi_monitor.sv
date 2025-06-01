class spi_monitor extends uvm_monitor;

    `uvm_component_utils(spi_monitor)

    virtual if_spi vif;
    uvm_analysis_port #(spi_packet) mon_analysis_port;

    // data collection variables
    int nfft;
    bit [7:0] mosi;
    bit [3:0] reg_response;
    bit [15:0] mem_response [$];

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_spi)::get(this, "", "", vif))
            `uvm_fatal("MON", "Virtual interface not found for SPI Monitor")
        if (!uvm_config_db#(int)::get(this, "", "nfft", nfft))
            `uvm_fatal("MON", "NFFT not found for SPI Monitor")
    endfunction

    virtual task run_phase(uvm_phase phase);
        forever begin
            spi_packet item = new();
            collect_transaction(item);
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(spi_packet item);
        @(negedge vif.csb);
        collect_signals(item);
    endtask

    virtual task collect_signals(spi_packet item);
        if (!uvm_config_db#(int)::get(this, "", "nfft", nfft)) begin
            `uvm_fatal("MON", "NFFT not found for SPI Monitor")
        end
        mem_response = {};
        reg_response = 4'h0;
        mosi = 8'h00;
        // collect MOSI data
        for (int i = 7; i >= 0; i--) begin
            @(posedge vif.scl);
            mosi[i] = vif.mosi;
        end

        item.command = mosi[7:6];
        item.reg_index = mosi[5:4];
        item.mosi_data = mosi[3:0];

        // receive MISO data
        if (item.command == 2'b10) begin : receive_mem
            for (int i = 0; i < nfft; i++) begin
                bit [15:0] reg_temp;
                for (int j = 15; j >= 0; j--) begin
                    @(posedge vif.scl);
                    reg_temp[i] = vif.miso;
                end
                item.mem_response.push_back(reg_temp);
            end
        end else begin
            for (int i = 3; i >= 0; i--) begin
                @(posedge vif.scl);
                item.reg_response[i] = vif.miso;
            end
        end

    endtask
endclass
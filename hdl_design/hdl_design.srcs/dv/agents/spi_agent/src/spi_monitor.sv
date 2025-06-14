class spi_monitor extends uvm_monitor;

    `uvm_component_utils(spi_monitor)

    virtual if_spi vif;
    uvm_analysis_port #(spi_packet) mon_analysis_port;

    // data collection variables
    int nfft;
    bit [7:0] mosi;
    bit [3:0] reg_response;
    bit [15:0] mem_response [$];

    bit CPOL;
    bit CPHA;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_spi)::get(this, "", "vif", vif))
            `uvm_fatal("MON", "Virtual interface not found for SPI Monitor")
        if (!uvm_config_db #(int)::get(this, "", "nfft", nfft))
            `uvm_fatal("MON", "Could not attach monitor NFFT")
        if (!uvm_config_db #(bit)::get(this, "", "CPOL", CPOL))
            `uvm_fatal("MON", "Could not attach monitor CPOL")
        if (!uvm_config_db #(bit)::get(this, "", "CPHA", CPHA))
            `uvm_fatal("MON", "Could not attach monitor CPHA")
    endfunction

    virtual task run_phase(uvm_phase phase);
        spi_packet item;
        forever begin
            item = new();
            collect_transaction(item);
            if (item.command == 2'h2)
                item.print();
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(spi_packet item);
        @(negedge vif.csb);
        `uvm_info("MON", "Collecting SPI Packet", UVM_HIGH)
        collect_signals(item);
    endtask

    virtual task collect_signals(spi_packet item);
        bit [15:0] reg_temp;
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
                reg_temp = 16'h0000;
                for (int j = 15; j >= 0; j--) begin
                    @(posedge vif.scl);
                    reg_temp[j] = vif.miso;
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
`timescale 1ns / 1ns

class spi_driver extends uvm_driver #(spi_packet);

    `uvm_component_utils(spi_driver)

    spi_packet req;

    virtual if_spi vif;
    int nfft;

    bit CPOL;
    bit CPHA;

    real speed;
    real clk_period_ns;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual if_spi)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "Could not attach driver virtual interface")
        if (!uvm_config_db #(int)::get(this, "", "nfft", nfft))
            `uvm_fatal("DRV", "Could not attach driver NFFT")
        if (!uvm_config_db #(bit)::get(this, "", "CPOL", CPOL))
            `uvm_fatal("DRV", "Could not attach driver CPOL")
        if (!uvm_config_db #(bit)::get(this, "", "CPHA", CPHA))
            `uvm_fatal("DRV", "Could not attach driver CPHA")
        if (!uvm_config_db #(int)::get(this, "", "speed", speed))
            `uvm_fatal("DRV", "Could not attach driver speed")
        clk_period_ns = 1e9 / speed;
    endfunction

    virtual task run_phase(uvm_phase phase);
        vif.csb = 1'b1; // SPI off to start
        vif.scl = 1'b0; // SPI mode 0 CPHA idle
        vif.mosi = 1'b0;
        forever begin
            seq_item_port.get_next_item(req);
            `uvm_info("DRV", "Driving SPI packet", UVM_HIGH)
            drive_signals(req);
            seq_item_port.item_done();
        end
    endtask

    // drive with 5 MHz clock, which is 200ns
    virtual task drive_signals(spi_packet req);
        bit [7:0] mosi = {req.command, req.reg_index, req.mosi_data};

        #(clk_period_ns/2);
        vif.csb = 1'b0;
        #(clk_period_ns/2);

        // send MOSI data
        for (int i = 7; i >= 0; i--) begin
            vif.mosi = mosi[i]; // MSB first
            #(clk_period_ns/2);
            vif.scl = 1'b1;
            #(clk_period_ns/2);
            vif.scl = 1'b0;
        end
        vif.mosi = 1'b0; // drive low to avoid MOSI staying high and being confusing

        // receive MISO data
        if (req.command == 2'b10) begin : receive_mem
            for (int i = 0; i < nfft; i++) begin
                bit [15:0] reg_temp;
                for (int j = 15; j >= 0; j--) begin
                    #(clk_period_ns/2);
                    vif.scl = 1'b1;
                    reg_temp[i] = vif.miso;
                    #(clk_period_ns/2);
                    vif.scl = 1'b0;
                end
                req.mem_response.push_back(reg_temp);
            end
        end else begin
            for (int i = 3; i >= 0; i--) begin
                #(clk_period_ns/2);
                vif.scl = 1'b1;
                req.reg_response[i] = vif.miso;
                #(clk_period_ns/2);
                vif.scl = 1'b0;
            end
        end

        #50;
        vif.csb = 1'b1;

    endtask

endclass
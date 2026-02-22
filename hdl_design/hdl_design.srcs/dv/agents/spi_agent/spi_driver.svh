`timescale 1ns / 1ns
/**
Class: spi_driver

Drives SPI packets onto the virtual interface. Could be configured to provide
responses, but not necessarily.
*/
class spi_driver extends uvm_driver #(spi_packet);

    `uvm_component_utils(spi_driver)

    spi_packet req;

    virtual if_spi vif;

    real speed;
    real clk_period_ns;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual if_spi)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "Could not attach driver virtual interface")
        if (!uvm_config_db #(int)::get(this, "", "clk_speed_hz", speed))
            `uvm_fatal("DRV", "Could not attach driver speed")
        clk_period_ns = 1e9 / speed;
    endfunction

    virtual task run_phase(uvm_phase phase);
        spi_packet req_copy;

        req_copy = spi_packet::type_id::create("driver_spi_pkt_copy");

        vif.csb = 1'b1; // SPI off to start
        vif.scl = 1'b0; // SPI mode 0 CPHA idle
        vif.mosi = 1'b0;
        forever begin
            seq_item_port.get_next_item(req);
            drive_signals(req);
            seq_item_port.item_done(req);
        end
    endtask

    // drive with 5 MHz clock, which is 200ns
    virtual task drive_signals(spi_packet req);
        bit [15:0] mosi = {req.rd_en, req.address};
        bit [15:0] reg_temp;

        `uvm_info("DRV", "Driving SPI packet", UVM_HIGH);
        req.print();

        #(clk_period_ns/2);
        vif.csb = 1'b0;
        #(clk_period_ns/2);

        // send bit and address
        for (int i = 15; i >= 0; i--) begin
            vif.mosi = mosi[i]; // MSB first
            #(clk_period_ns/2);
            vif.scl = 1'b1;
            #(clk_period_ns/2);
            vif.scl = 1'b0;
        end

        // receive MISO data
        if (req.rd_en == 1'b1) begin : read_reg
            vif.mosi = 1'b0; // drive low to avoid MOSI staying high and being confusing
            req.read_data.delete();
            for (int i = 0; i < req.n_reads; i++) begin
                reg_temp = 16'h0000;
                for (int j = 15; j >= 0; j--) begin
                    #(clk_period_ns/2);
                    vif.scl = 1'b1;
                    reg_temp[j] = vif.miso;
                    #(clk_period_ns/2);
                    vif.scl = 1'b0;
                end
                req.read_data.push_back(reg_temp);
            end
        end else begin : write_reg
            for (int j = 0; j < req.write_data.size(); j++) begin
                mosi = req.write_data[j];
                for (int i = 15; i >= 0; i--) begin
                    vif.mosi = mosi[i]; // MSB first
                    #(clk_period_ns/2);
                    vif.scl = 1'b1;
                    #(clk_period_ns/2);
                    vif.scl = 1'b0;
                end
            end
        end

        #(clk_period_ns/2);
        vif.csb = 1'b1;
        #(clk_period_ns/2);

    endtask

endclass
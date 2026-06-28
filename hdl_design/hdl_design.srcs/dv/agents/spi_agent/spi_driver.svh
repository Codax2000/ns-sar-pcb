`timescale 1ns / 1ns
/**
Class: spi_driver

Drives SPI packets onto the virtual interface. Could be configured to provide
responses, but not necessarily.
*/
class spi_driver extends uvm_driver #(spi_packet);

    `uvm_component_utils(spi_driver)

    spi_packet req;

    virtual spi_if vif;

    real clk_period_ns;

    bit cpol;
    bit cpha;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        real speed;
        if (!uvm_config_db #(virtual spi_if)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "Could not attach driver virtual interface")
        if (!uvm_config_db #(int)::get(this, "", "clk_speed_hz", speed))
            `uvm_fatal("DRV", "Could not attach driver speed")
        if (!uvm_config_db #(bit)::get(this, "", "cpol", cpol))
            `uvm_fatal("DRV", "Could not attach driver CPOL")
        if (!uvm_config_db #(bit)::get(this, "", "cpha", cpha))
            `uvm_fatal("DRV", "Could not attach driver CPHA")
        clk_period_ns = 1e9 / speed;
    endfunction

    virtual task run_phase(uvm_phase phase);

        vif.csb = 1'b1; // SPI off to start
        forever begin
            seq_item_port.get_next_item(req);
            drive_item(req);
            seq_item_port.item_done(req);
        end
    endtask
/*
    Task: drive_item
    Executes a single SPI transaction packet onto the virtual interface.
    */
    virtual task drive_item(spi_packet pkt);
        real half_period_ns;
        half_period_ns = clk_period_ns / 2.0;
        logic [7:0] tx_byte;
        logic [7:0] rx_byte;

        pkt.miso.delete();

        // Assert Chip Select (Active Low)
        vif.scl = 0;
        #(half_period_ns);
        vif.cs_n <= 1'b0;

        // Loop through every byte in the packet payload
        foreach (pkt.mosi[byte_idx]) begin
            tx_byte = pkt.mosi[byte_idx];
            rx_byte = 8'h00;

            // Shift out 8 bits (MSB first standard)
            for (int bit_idx = 7; bit_idx >= 0; bit_idx--) begin
                vif.mosi = tx_byte[bit_idx];
                #(half_period_ns);
                vif.scl = 1;
                rx_byte[bit_idx] = vif.mosi;
                #(half_period_ns);
                vif.scl = 0;
            end
            
            // Capture the received byte back into the transaction packet
            pkt.miso.push_back(rx_byte);
        end

        // De-assert Chip Select
        #(half_period_ns);
        vif.cs_n <= 1'b1;
        #(half_period_ns);
        
    end task : drive_item

endclass
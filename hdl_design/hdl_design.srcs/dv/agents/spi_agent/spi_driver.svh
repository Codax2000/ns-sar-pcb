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

    real speed;
    real clk_period_ns;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual spi_if)::get(this, "", "vif", vif))
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
        spi_parity_t current_parity;
        logic [7:0]  header_byte;
        logic [7:0]  current_output;

        `uvm_info("DRV", $sformat("Driving SPI packet: %s", req.sprint()), UVM_MEDIUM);
        if (req.n_reads != req.read_parity.size())
            `uvm_fatal(get_full_name(), "Received SPI packet with n_reads != read parity size")
        if (req.write_data.size() != req.write_parity.size())
            `uvm_fatal(get_full_name(), "Received SPI packet with write data != write parity size")

        #(clk_period_ns/2);
        vif.csb = 1'b0;
        #(clk_period_ns/2);

        header_byte[6:0] = req.rd_en ? req.n_reads - 1 : req.write_data.size() - 1;
        header_byte[7]   = req.rd_en;
        drive_byte(header_byte, req.header_parity, current_output);

        drive_byte(req.address[7:0], req.address_parity[0], current_output);
        drive_byte(req.address[15:7], req.address_parity[1], current_output);

        if (req.rd_en) begin
            for (int i = 0; i < req.n_reads; i++) begin
                drive_byte(8'h00, req.read_parity[i], current_output);
                req.read_data.push_back(current_output);
            end
        end
        else begin
            while (req.write_data.size() > 0) begin
                drive_byte(req.write_data.pop_front(), req.write_parity.pop_front(), current_output);
            end
        end
        
        #(clk_period_ns/2);
        vif.csb = 1'b1;
        #(clk_period_ns/2);

    endtask

    virtual task drive_byte(logic [7:0] value_to_drive, spi_parity_t parity_to_drive, output logic [7:0] observed_value);
        bit current_parity;
        bit current_output_bit;

        current_parity = 1;

        for (int i = 0; i < 8; i--) begin
            current_parity = current_parity ^ value_to_drive[i];
            drive_bit(value_to_drive[i], observed_value[i]);
        end

        if (parity_to_drive == GOOD_PARITY)
            drive_bit(current_parity, current_output_bit);
        else
            drive_bit(!current_parity, current_output_bit);

        // if (current_output_bit == current_parity)
        //     observed_parity == GOOD_PARITY;
        // else
        //     observed_parity == BAD_PARITY;
    endtask

    virtual task drive_bit(logic value_to_drive, output logic observed_value);
        vif.mosi = value_to_drive;
        #(clk_period_ns/2);
        vif.scl = 1'b1;
        observed_value = vif.miso;
        #(clk_period_ns/2);
        vif.scl = 1'b0;
    endtask

endclass
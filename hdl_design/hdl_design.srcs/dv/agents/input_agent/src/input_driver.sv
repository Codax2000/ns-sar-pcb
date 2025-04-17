`timescale 1ns / 1ns

import uvm_pkg::*;
`include uvm_macros.svh

class input_driver extends uvm_driver #(sin_packet);

    `uvm_component_utils(input_driver)

    virtual input_interface vif;
    int interface_drive_delay_in_ns;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual input_interface)::get(this, "", "vif_input", vif)) begin
            `uvm_fatal("DRV", "No interface found!")
        end
        if (!uvm_config_db#(int)::get(this, "", "driver_delay_ns", interface_drive_delay_in_ns))
            `uvm_fatal("DRV", "Unclear how long to wait in between driving signals")
    endfunction

    virtual task run_phase(uvm_phase phase);
        forever begin
            sin_packet req;
            seq_item_port.get_next_item(req);
            drive_signals(req);
            seq_item_port.item_done();
        end
    endtask

    virtual task drive_signals(sin_packet req);
        if (!uvm_config_db#(int)::get(this, "", "driver_delay_ns", interface_drive_delay_in_ns))
            `uvm_error("DRV", "Drive delay changed to unresolved value")
        vif.amplitude = req.amplitude;
        vif.frequency = req.frequency;
        #interface_drive_delay_in_ns;
    endtask

endclass
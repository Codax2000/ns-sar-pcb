`timescale 1ns / 1ps

class input_driver extends uvm_driver #(sin_packet);

    `uvm_component_utils(input_driver)

    sin_packet req;

    virtual if_input vif;
    real vdd;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_input)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "Could not attach virtual interface")
        if (!uvm_config_db#(real)::get(this, "", "vdd", vdd))
            `uvm_fatal("DRV", "Could not attach sampling frequency")
    endfunction

    virtual task run_phase(uvm_phase phase);
        vif.vcm = vdd / 2;
        forever begin
            seq_item_port.get_next_item(req);
            drive_signals(req);
            seq_item_port.item_done();
        end
    endtask

    virtual task drive_signals(sin_packet req);
        vif.amplitude = req.amplitude;
        vif.frequency = req.frequency;
        vif.values_changed = 1'b1;
        #1;
        vif.values_changed = 1'b0;
    endtask

endclass
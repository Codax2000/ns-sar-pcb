`timescale 1ns / 1ns

class input_driver extends uvm_driver #(sin_packet);

    `uvm_component_utils(input_driver)

    virtual input_interface vif;

    real phase;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        phase = 0;
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual input_interface)::get(this, "", "vif", vif)) begin
            `uvm_fatal("DRV", "No interface found!")
        end
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
        vif.amplitude = req.amplitude;
        vif.frequency = req.frequency;
    endtask

endclass
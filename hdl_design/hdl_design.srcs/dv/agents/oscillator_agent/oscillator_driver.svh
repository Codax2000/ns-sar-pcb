/**
Class: oscillator_driver

Drives <oscillator_packet>s onto the oscillator interface.
*/
class oscillator_driver extends uvm_driver #(oscillator_packet);

    `uvm_component_utils(oscillator_driver)

    oscillator_packet req;

    virtual oscillator_if vif;

    function new (string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual oscillator_if)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "Could not attach driver virtual interface")
    endfunction

    virtual task run_phase(uvm_phase phase);
        vif.stop_clock(0);
        forever begin
            seq_item_port.get_next_item(req);
            drive_signals(req);
            seq_item_port.item_done(req);
        end
    endtask

    virtual task drive_signals(oscillator_packet req);
        `uvm_info(get_full_name(), $sformatf("Driving new packet: %s", req.sprint()), UVM_MEDIUM)
        if (req.enabled)
            vif.start_clock(req.frequency);
        else
            vif.stop_clock(req.disabled_state);
    endtask

endclass
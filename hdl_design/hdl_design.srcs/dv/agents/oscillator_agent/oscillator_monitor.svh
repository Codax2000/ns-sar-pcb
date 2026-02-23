/**
Class: oscillator_monitor

Monitors the oscillator interface and reports any changes in frequency or
enabled status.
*/
class oscillator_monitor extends uvm_monitor;

    `uvm_component_utils(oscillator_monitor)

    oscillator_packet pkt;
    virtual oscillator_if vif;
    uvm_analysis_port #(oscillator_packet) mon_analysis_port;
    real frequency_threshold;

    bit current_enable;
    real current_frequency;
    bit current_disabled_state;

    function new (string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual oscillator_if)::get(this, "", "vif", vif))
            `uvm_fatal(get_full_name(), "Virtual interface not found")
        if (!uvm_config_db #(real)::get(this, "", "frequency_threshold", frequency_threshold))
            `uvm_fatal(get_full_name(), "Could not find frequency threshold")
        if (!uvm_config_db #(real)::get(this, "", "timeout_time_ns", vif.timeout_time_ns))
            `uvm_fatal(get_full_name(), "Could not find timeout time")
    endfunction

    virtual task run_phase (uvm_phase phase);
        bit did_publish;

        current_enable = 0;
        current_frequency = 0.0;
        current_disabled_state = 0;
        
        pkt = oscillator_packet::type_id::create("mon_packet", this);

        forever begin
            collect_transaction(pkt);
            publish_transaction_if_needed(pkt, did_publish);
        end
    endtask

    virtual task collect_transaction(ref oscillator_packet item);
        @(vif.clk_enable_observed or vif.frequency_observed or vif.disabled_state_observed);
        item.enabled = vif.clk_enable_observed;
        item.frequency = vif.frequency_observed;
        item.disabled_state = vif.disabled_state_observed;
    endtask

    virtual task publish_transaction_if_needed (ref oscillator_packet item, output bit did_publish);
        real frequency_difference;
        
        did_publish = 0;

        if (item.enabled != current_enable) begin
            `uvm_info(get_full_name(), $sformatf("New oscillator packet based on enable: %s",
                                                 item.sprint()), UVM_HIGH)
            publish_item(item);
            did_publish = 1;
        end else if ((!item.enabled) && (item.disabled_state != current_disabled_state)) begin // both disabled, report new disabled state
            `uvm_info(get_full_name(), $sformatf("New oscillator packet based on disabled state: %s",
                                                 item.sprint()), UVM_HIGH)
            publish_item(item);
            did_publish = 1;
        end else if (item.enabled) begin
            frequency_difference = current_frequency - item.frequency;
            frequency_difference = frequency_difference < 0 ? -frequency_difference : frequency_difference;
            if (frequency_difference > frequency_threshold) begin
                `uvm_info(get_full_name(), $sformatf("New oscillator packet based on frequency with large delta: %s",
                                                 item.sprint()), UVM_HIGH)
                publish_item(item);
                did_publish = 1;
            end else
                `uvm_info(get_full_name(), $sformatf("No new oscillator packet because frequency delta is too small: %s",
                                                     item.sprint()), UVM_HIGH)
        end else
            `uvm_info(get_full_name(), "New packet but insufficient reason for oscillator_monitor to publish.", UVM_HIGH)
    endtask

    virtual task publish_item (oscillator_packet item);
        current_frequency = item.frequency;
        current_enable = item.enabled;
        current_disabled_state = item.disabled_state;

        mon_analysis_port.write(item);

        item = oscillator_packet::type_id::create("mon_packet", this);
    endtask

endclass
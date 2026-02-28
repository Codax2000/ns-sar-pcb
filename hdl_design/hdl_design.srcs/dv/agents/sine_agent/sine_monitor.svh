/**
Class: sine_monitor

Monitor capable of reporting sine wave amplitudes as well as frequency and such.
*/
class sine_monitor extends oscillator_monitor;

    `uvm_component_utils(sine_monitor)

    sine_proxy vproxy;

    sine_packet ms_pkt;

    real amplitude_threshold;
    real current_amplitude;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (! uvm_config_db #(sine_proxy)::get(this, "", "vproxy", vproxy))
            `uvm_fatal(get_full_name(), "Could not find proxy")
        if (! uvm_config_db #(real)::get(this, "", "amplitude_threshold", amplitude_threshold))
            `uvm_fatal(get_full_name(), "Could not find amplitude threshold")
    endfunction

    virtual task run_phase (uvm_phase phase);
        current_amplitude = 0.0;
        super.run_phase(phase);
    endtask

    virtual task collect_transaction(ref oscillator_packet item);
        ms_pkt = sine_packet::type_id::create("ms_pkt");

        @(vif.clk_enable_observed or vif.frequency_observed or vif.disabled_state_observed or vproxy.amplitude);
        ms_pkt.enabled = vif.clk_enable_observed;
        ms_pkt.frequency = vif.frequency_observed;
        ms_pkt.disabled_state = vif.disabled_state_observed;

        vproxy.sample(ms_pkt.amplitude);

        item = ms_pkt;
    endtask

    virtual task publish_transaction_if_needed(ref oscillator_packet item, output bit did_publish);
        real amplitude_difference;
        
        did_publish = 0;
        super.publish_transaction_if_needed(item, did_publish);

        if (! $cast(ms_pkt, item))
            `uvm_ms_fatal(get_full_name(), "Could not cast item to mixed-signal equivalent")

        amplitude_difference = ms_pkt.amplitude - current_amplitude;
        amplitude_difference = amplitude_difference < 0.0 ? -amplitude_difference : amplitude_difference;

        if ((!did_publish) && (amplitude_difference > amplitude_threshold)) begin
            this.current_amplitude = ms_pkt.amplitude;
            publish_item(item);
        end
    endtask

endclass




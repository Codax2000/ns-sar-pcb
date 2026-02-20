/**
Class: sine_agent

Provides configuration for driver and monitor, and also adds coverage collection
for mixed-signal sine waves instead of just normal ones.
*/
class sine_agent extends oscillator_agent;

    `uvm_component_utils(sine_agent)

    function new (string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    sine_coverage_collector m_sine_coverage_collector;

    virtual function void build_phase(uvm_phase phase);
        uvm_config_db #(int)::set(this, "driver", "")
    endfunction

endclass
/**
Class: sine_agent_cfg

Extension of the <oscillator_agent_cfg> that contains the proxy necessary
for mixed-signal agents.
*/
class sine_agent_cfg extends oscillator_agent_cfg;

    // Variable: vproxy
    // Proxy used by the driver and monitor to configure mixed-signal values
    sine_proxy vproxy;

    // Variable: amplitude_threshold
    // Like frequency detection threshold, but with amplitude
    real amplitude_threshold;

    `uvm_object_utils_begin(sine_agent_cfg)
        `uvm_field_real(amplitude_threshold)
    `uvm_object_utils_end

    function new(string name = "sine_agent_cfg");
        super.new(name);
    endfunction

endclass
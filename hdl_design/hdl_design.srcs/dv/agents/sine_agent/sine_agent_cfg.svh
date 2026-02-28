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

    // Variable: points_per_period
    // The number of points driven per oscillation period, like FFT sampling.
    // Also like FFT, more points -> more precise but also longer sim time.
    // Recommend to use multiples of 4 to get a precise min and max.
    int points_per_period;

    `uvm_object_utils_begin(sine_agent_cfg)
        `uvm_field_real(amplitude_threshold, UVM_ALL_ON)
        `uvm_field_int(points_per_period, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "sine_agent_cfg");
        super.new(name);
    endfunction

endclass
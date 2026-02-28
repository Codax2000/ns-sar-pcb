/**
Class: sine_proxy

Proxy used by sine wave driver and monitor for AMS communication. Must be
implemented in the bridge.
*/
virtual class sine_proxy extends uvm_ms_proxy;

    // Group: Driver

    // Function: push
    // Send the given amplitude to be driven by the bridge
    virtual task push(real amplitude);
        `uvm_ms_warning("SINE PROXY", "Function push not implemented")
    endtask

    // Function: configure_driver
    // Set any config values that the driver needs
    virtual function void configure_driver (int points_per_period);
        `uvm_ms_warning("SINE PROXY", "Function configure_driver not implemented")
    endfunction

    // Group: Monitor

    // Variable: amplitude
    // Changes when a new amplitude is available.
    real amplitude;

    // Function: sample
    // Get the amplitude observed by the bridge, but after waiting for a peak
    // or trough if the clock is enabled. This is intended to allow for
    // changes in frequency as well as amplitude. If the clock is disabled,
    // wait for the wave to stabilize before sampling. 
    //
    // Parameters:
    //   amplitude - output amplitude read by the task.
    virtual task sample(output real amplitude);
        `uvm_ms_warning("SINE PROXY", "Function sample not implemented")
    endtask

endclass
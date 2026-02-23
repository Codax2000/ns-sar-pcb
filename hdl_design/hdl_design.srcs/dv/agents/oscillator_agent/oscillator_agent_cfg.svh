/**
Class: oscillator_agent_cfg

Config for the digial-only oscillator agent. Contains the threshold for changes
in frequency to be reported.
*/
class oscillator_agent_cfg extends uvm_object;

    // Variable: vif
    // Virtual interface the agent will use
    virtual oscillator_if vif;

    // Variable: is_active
    // If set to UVM_ACTIVE, agent will instantiate driver and sequencer with the assumption
    // that they will be used to drive signals.
    uvm_active_passive_enum is_active;

    // Variable: checks_enable
    // Boilerplate variable that, if 1, will enable any internal checks that the agent has.
    bit checks_enable;

    // Variable: coverage_enable
    // If 1, the agent will instantiate a uvm_subscriber that will collect coverage data
    // on received packets.
    bit coverage_enable;

    // Variable: frequency_threshold
    // Threshold as a fraction of current frequency below which frequency differences 
    // from the current observed frequency will not be reported, i.e. allowable
    // frequency mismatch.
    real frequency_threshold;

    // Variable: timeout_time_ns
    // The time in ns before which the monitor will not report a disabled clock
    int timeout_time_ns;

    `uvm_object_utils_begin(oscillator_agent_cfg)
        `uvm_field_int(checks_enable, UVM_ALL_ON)
        `uvm_field_int(coverage_enable, UVM_ALL_ON)
        `uvm_field_real(frequency_threshold, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "oscillator_agent_cfg");
        super.new(name);
    endfunction

endclass
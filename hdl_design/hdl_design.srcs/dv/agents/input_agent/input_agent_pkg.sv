package input_agent_pkg;
    import uvm_pkg::*;
    `include "input_agent.sv"
    `include "input_driver.sv"
    `include "input_monitor.sv"
    `include "input_sequencer.sv"
    `include "sin_packet.sv"
    `include "const_packet.sv"
    `include "drive_random_values.sv"
    `include "drive_sin_wave.sv"
endpackage
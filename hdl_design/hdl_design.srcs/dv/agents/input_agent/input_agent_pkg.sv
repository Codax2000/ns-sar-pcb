package input_agent_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    `include "sin_packet.sv"
    `include "const_packet.sv"
    `include "input_driver.sv"
    `include "input_monitor.sv"
    `include "input_sequencer.sv"
    `include "sequences/drive_random_values.sv"
    `include "sequences/drive_sin_wave.sv"
    `include "input_agent.sv"
endpackage
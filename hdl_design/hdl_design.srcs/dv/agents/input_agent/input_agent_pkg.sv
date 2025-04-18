package input_agent_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    `include "data_items/sin_packet.sv"
    `include "data_items/const_packet.sv"
    `include "src/input_driver.sv"
    `include "src/input_monitor.sv"
    `include "src/input_sequencer.sv"
    `include "sequences/drive_random_values.sv"
    `include "sequences/drive_sin_wave.sv"
    `include "input_agent.sv"
endpackage
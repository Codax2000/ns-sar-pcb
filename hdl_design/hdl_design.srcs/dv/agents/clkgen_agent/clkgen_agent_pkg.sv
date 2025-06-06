package clkgen_agent_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    `include "data_items/clkgen_packet.sv"
    `include "sequences/clkgen_seq_lib.sv"
    `include "src/clkgen_driver.sv"
    `include "src/clkgen_monitor.sv"
    `include "clkgen_sequencer.sv"
    `include "clkgen_agent.sv"
endpackage
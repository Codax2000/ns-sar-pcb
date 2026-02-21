package adc_env_pkg;

    // include UVM package/macros
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // TODO: include UVM-MS

    // TODO: include agent packages and RAL

    // eventually, include scoreboard package

    // include multichannel sequencer
    `include "adc_mc_sequencer.svh"
    `include "adc_mc_seq_lib.svh"

    // finally, include environment
    `include "adc_env_cfg.sv"
    `include "adc_env.sv"

endpackage
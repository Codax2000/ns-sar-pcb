package adc_env_pkg;

    // include UVM package/macros
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // include agent packages
    import spi_agent_pkg::*;

    import input_agent_pkg::*;

    import clkgen_agent_pkg::*;

    // include RAL
    `include "reg2spi_adapter.sv"
    `include "ral_cfg.sv"
    `include "reg_env.sv"

    // eventually, include scoreboard package

    // include multichannel sequencer
    `include "adc_mc_sequencer.sv"
    `include "adc_mc_seq_lib.sv"

    // finally, include environment
    `include "adc_env_cfg.sv"
    `include "adc_env.sv"

endpackage
/**
Package: adc_env_pkg

Package containing reusable environment for an ADC verification environment. The
ADC has clock and reset agents, plus SPI and a differential input agent written
in UVM-MS.

It also contains sequences for running different types of ADC conversion,
assuming that register names are consistent. This likely isn't true, but there
should be ways of avoiding entirely rewriting the sequence by extending them
and using inheritance.

Users should have the following compiled before compiling this package:

- uvm_pkg
- uvm_ms_pkg
- <bit_bus_agent_pkg>
- <spi_agent_pkg>
- <oscillator_agent_pkg>
- <sine_agent_pkg>
- <reg_env_pkg>

This env defines the following classes:

- <adc_mc_sequencer>
- <adc_mc_seq_lib>
- <adc_env_cfg>
- <adc_env>
*/
package adc_env_pkg;

    // include UVM package/macros
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // include UVM-MS
    import uvm_ms_pkg::*;
    `include "uvm_ms.svh"

    // Include agent packages and RAL
    import bit_bus_agent_pkg::*;
    import spi_agent_pkg::*;
    import oscillator_agent_pkg::*;
    import sine_agent_pkg::*;
    import reg_env_pkg::*;

    // TODO: eventually, include scoreboard package

    // TODO: include multichannel sequencer once completed
    // `include "adc_mc_sequencer.svh"
    // `include "adc_mc_seq_lib.svh"

    // finally, include environment
    `include "adc_env_cfg.svh"
    `include "adc_env.svh"

endpackage
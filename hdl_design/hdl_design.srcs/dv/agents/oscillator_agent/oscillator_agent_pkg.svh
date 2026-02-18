/**
Package: oscillator_agent_pkg

Contains all the necessary classes for the oscillator agent. Users must also
make sure that the oscillator interface, <oscillator_if>, is compiled.

Necessary classes:

    - <oscillator_packet>
    - <oscillator_single_packet_seq>
    - <oscillator_driver>
    - <oscillator_monitor>
    - <oscillator_coverage_collector>
    - <oscillator_agent>
*/
package oscillator_agent_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    `include "oscillator_packet.svh"
    `include "oscillator_seq_lib.svh"
    `include "oscillator_driver.svh"
    `include "oscillator_monitor.svh"
    `include "oscillator_coverage_collector.svh"
    `include "oscillator_agent.svh"

endpackage
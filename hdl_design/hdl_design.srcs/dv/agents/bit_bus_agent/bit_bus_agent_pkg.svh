/**
Package: bit_bus_agent_pkg

Parametrizable bit/bus agent for driving and monitoring generic digital
control signals. Intended for use in environments requiring simple 1‑bit
or N‑bit digital stimulus, such as reset lines, enables, or low‑complexity
digital control/status buses.

This package requires that <bit_bus_if> be compiled. 

Included classes are:
  - <bit_bus_packet>
  - <bit_bus_driver> 
  - <bit_bus_monitor> 
  - <bit_bus_agent_cfg> 
  - <bit_bus_agent> 
*/
package bit_bus_agent_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    `include "bit_bus_packet.sv"
    `include "src/bit_bus_agent_cfg.sv"
    `include "src/bit_bus_driver.sv"
    `include "src/bit_bus_monitor.sv"
    `include "src/bit_bus_agent.sv"

endpackage
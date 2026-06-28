/**
Package: axi4lite_agent_pkg

AXI4-Lite agent package that contains supporting classes for burst read and write,
in addition to an adapter for RAL that is specific to this agent.

Includes the following classes:

- <axi4lite_packet>
- <axi4lite_packet_reg_extension>
- <axi4lite_driver>
- <axi4lite_monitor>
- <axi4lite_coverage>
- <axi4lite_agent_cfg>
- <axi4lite_agent>

*/
package axi4_lite_agent_pkg;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    typedef enum bit { 
        AXI_READ  = 1'b1, 
        AXI_WRITE = 1'b0 
    } axi_op_e;

    `include "axi4_lite_packet.svh"
    `include "axi4_lite_packet_reg_extension.svh"
    `include "axi4_lite_driver.svh"
    `include "axi4_lite_monitor.svh"
    `include "axi4_lite_coverage.svh"
    `include "axi4_lite_agent_cfg.svh"
    `include "axi4_lite_agent.svh"

endpackage
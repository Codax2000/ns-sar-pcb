/**
Package: spi_agent_pkg

SPI agent package that contains supporting classes for burst read and write,
in addition to an adapter for RAL that is specific to this agent.

Includes the following classes:

- <spi_packet>
- <spi_packet_reg_extension>
- <spi_driver>
- <spi_monitor>
- <spi_agent_cfg>
- <spi_agent>
- <spi_packet_splitter>
- <reg2spi_adapter>

*/
package spi_agent_pkg;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    `include "spi_packet.svh"
    `include "spi_packet_reg_extension.svh"
    `include "spi_driver.svh"
    `include "spi_monitor.svh"
    `include "spi_agent_cfg.svh"
    `include "spi_agent.svh"
    `include "spi_packet_splitter.svh"
    `include "reg2spi_adapter.svh"
endpackage
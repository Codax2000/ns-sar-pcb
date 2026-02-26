/**
Package: spi_agent_pkg

SPI agent package that contains supporting classes for burst read and write,
in addition to an adapter for RAL that is specific to this agent.

Since this is an extension of the <oscillator_agent>, requires that <oscillator_agent_pkg>
be compiled.

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

    typedef enum bit {
        BAD_PARITY = 0,
        GOOD_PARITY = 1
    } spi_parity_t;

    `include "spi_packet.svh"
    `include "spi_packet_reg_extension.svh"
    // `include "spi_driver.svh"
    // `include "spi_monitor.svh"
    `include "spi_agent_cfg.svh"
    `include "spi_agent.svh"
    `include "spi_packet_splitter.svh"
    `include "reg2spi_adapter.svh"
endpackage
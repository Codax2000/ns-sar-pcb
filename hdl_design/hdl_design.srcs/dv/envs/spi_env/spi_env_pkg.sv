/**
Package: spi_env_pkg

SPI environment package that contains supporting classes for the SPI environment.

Includes the following classes:

- <spi_env_cfg>
- <spi_env>
- <spi_reg_subscriber>

*/
package spi_env_pkg;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    import spi_agent_pkg::*;

    `include "spi_env_cfg.svh"
    `include "spi_reg_subscriber.svh"
    `include "spi_env.svh"
    
endpackage

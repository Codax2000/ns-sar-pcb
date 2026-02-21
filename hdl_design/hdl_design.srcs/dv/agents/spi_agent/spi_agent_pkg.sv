package spi_agent_pkg;
    import uvm_pkg::*;

    typedef enum bit {
        SPI_READ  = 1,
        SPI_WRITE = 0
    } packet_type_e;

    `include "uvm_macros.svh"
    `include "data_items/spi_packet.sv"
    `include "data_items/spi_packet_reg_extension.sv"
    `include "src/spi_driver.sv"
    `include "src/spi_monitor.sv"
    `include "spi_agent_cfg.sv"
    `include "spi_agent.sv"
    `include "reg2spi_adapter.sv"
endpackage
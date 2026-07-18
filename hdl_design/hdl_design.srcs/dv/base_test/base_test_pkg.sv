/**
Package: base_test_pkg

Contains the base test and associated configuration classes:

- <base_test_cfg>
- <tb_top_cfg>
- <base_test>

*/
package base_test_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    import bit_bus_agent_pkg::*;
    import oscillator_agent_pkg::*;
    import spi_agent_pkg::*;
    import chip_regs_dv_pkg::*;
    import reg_env_pkg::*;
    import spi_env_pkg::*;

    `include "tb_top_cfg.svh"
    `include "base_test_cfg.svh"
    `include "base_test.svh"

endpackage
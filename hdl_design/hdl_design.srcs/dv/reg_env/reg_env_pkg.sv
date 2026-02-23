/**
Package: reg_env_pkg

Contains a parametrized register environment <reg_env> that should be usable with any
RAL that does subscriber-based prediction.
*/
package reg_env_pkg;

    // include UVM package/macros
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    `include "adc_reg_field.svh"
    `include "reg_env.svh"

endpackage
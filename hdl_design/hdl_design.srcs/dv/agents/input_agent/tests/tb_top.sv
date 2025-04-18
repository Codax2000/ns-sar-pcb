module tb_top ();

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import input_agent_pkg::*;
    `include "input_test_lib.sv"

    if_input iut; // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "*", "vif_input", iut);
        run_test("base_test");
    end

endmodule
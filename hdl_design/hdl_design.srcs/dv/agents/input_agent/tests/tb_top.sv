import uvm_pkg::*;
import input_agent_pkg::*;
`include "uvm_macros.svh"

module tb_top ();

    if_input iut; // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "*", "vif_input", iut);
        run_test("base_test");
    end

endmodule
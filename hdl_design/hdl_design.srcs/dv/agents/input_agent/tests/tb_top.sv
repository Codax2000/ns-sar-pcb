import uvm_pkg::*;
import input_agent_pkg::*;

module tb_sine_wave ();

    if_input iut; // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "*", "vif_input", iut);
        run_test("base_test");
    end

endmodule
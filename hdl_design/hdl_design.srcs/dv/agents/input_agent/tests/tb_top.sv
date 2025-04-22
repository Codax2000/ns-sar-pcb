module tb_top ();

    import uvm_pkg::*;

    if_input iut (); // interface under test

    initial begin
        uvm_config_db #(virtual if_input)::set(null, "uvm_test_top.agent.*", "vif", iut);
        if (uvm_config_db #(virtual if_input)::exists(null, "uvm_test_top.agent.driver", "vif"))
            `uvm_info("CONFIG", "Virtual interface exists", UVM_LOW)
        else
            `uvm_info("CONFIG", "Virtual interface is not set", UVM_LOW)
        run_test("base_test");
    end

endmodule
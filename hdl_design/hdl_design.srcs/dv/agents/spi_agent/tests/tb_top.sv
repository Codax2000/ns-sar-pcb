module tb_top ();

    import uvm_pkg::*;

    if_spi iut (); // interface under test

    initial begin
        uvm_config_db #(virtual if_spi)::set(null, "uvm_test_top.agent.*", "vif", iut);
        run_test("spi_test");
    end

endmodule


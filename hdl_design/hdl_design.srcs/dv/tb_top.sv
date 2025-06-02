module tb_top ();

    if_clkgen i_if_clkgen;
    if_input i_if_input;
    if_spi i_if_spi;

    if_status i_if_status;

    // board_top DUT (
    //     // TODO: add test signals
    // );

    // TODO: connect status interface signals
    // assign i_if_status.fsm_convert_status = DUT.

    initial begin
        uvm_config_db #(virtual if_clkgen)::set(this, "env", "vif_clkgen", i_if_clkgen);
        uvm_config_db #(virtual if_input)::set(this, "env", "vif_input", i_if_input);
        uvm_config_db #(virtual if_spi)::set(this, "env", "vif_spi", i_if_spi);
        uvm_config_db #(virtual if_status)::set(this, "env", "vif_status", i_if_status);

        run_test("base_test");
    end

endmodule
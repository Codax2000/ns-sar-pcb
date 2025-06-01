module tb_top ();

    if_clkgen i_if_clkgen;
    if_input i_if_input;
    if_spi i_if_spi;

    if_status i_if_status;

    board_top DUT (
        // TODO: add test signals
    );

    initial begin
        // TODO: add whatever interfaces there are to the TEST library, not directly to the monitors
        run_test("base_test")
    end

endmodule
import uvm_pkg::*;
`include "uvm_macros.svh"

import 

module tb_top ();

    if_clkgen i_if_clkgen();
    if_input i_if_input();
    if_spi i_if_spi();

    if_status i_if_status();

    // board_top DUT (
    //     // TODO: add test signals
    // );

    // TODO: connect status interface signals
    // assign i_if_status.fsm_convert_status = DUT.

    top_cfg cfg;

    initial begin
        cfg = new("top_cfg");
        cfg.vif_spi = i_if_spi;
        cfg.vif_clkgen = i_if_clkgen;
        cfg.vif_input = i_if_input;
        cfg.vif_status = i_if_status;

        uvm_config_db #(top_cfg)::set(null, "*", "top_cfg", cfg);

        run_test("base_test");
    end

endmodule
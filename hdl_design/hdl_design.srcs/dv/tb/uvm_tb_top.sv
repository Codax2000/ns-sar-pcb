`timescale 1ns/1ps

import uvm_pkg::*;
`include "uvm_macros.svh"

import test_pkg::*;

module uvm_tb_top ();

    if_clkgen i_if_clkgen();
    if_input i_if_input();
    if_spi i_if_spi();

    if_status i_if_status();

    board_top DUT (
        .vin(i_if_input.hardware_port),
        .clkgen(i_if_clkgen.module_clkgen),
        .spi(i_if_spi)
    );

    // TODO: connect status interface signals
    // assign i_if_status.fsm_convert_status = DUT.
    assign i_if_status.fsm_convert_status = 2'b00;
    assign i_if_status.rst_b = DUT.DIGTOP.sys_rst_b;

    tb_top_cfg cfg;
    assign i_if_spi.miso = 1'b0;

    initial begin
        cfg = new("tb_top_cfg");
        cfg.vif_spi = i_if_spi;
        cfg.vif_clkgen = i_if_clkgen;
        cfg.vif_input = i_if_input;
        cfg.vif_status = i_if_status;

        uvm_config_db #(tb_top_cfg)::set(null, "*", "tb_top_cfg", cfg);

        run_test("base_test");
    end

endmodule
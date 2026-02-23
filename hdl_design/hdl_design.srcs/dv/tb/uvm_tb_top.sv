`timescale 1ns/1ps

import uvm_pkg::*;
`include "uvm_macros.svh"

import base_test_pkg::*;

/**
Module: uvm_tb_top

Toplevel static module. Instantiates the board as the DUT instead of the digital only,
with the board as a wrapper around digital.

Instantiates bridge and interfaces and runs the current test.
*/
module uvm_tb_top ();

    bit_bus_if #(.WIDTH(1)) i_reset_if ();
    oscillator_if           i_clk_if   ();
    spi_if                  i_spi_if   ();

    status_if i_status_if ();

    // Variable: VDD
    // Parametrized supply voltage of the design
    localparam VDD = 1.2;
    real       vinp;
    real       vinn;

    sine_ms_bridge m_bridge (
        .vdd(VDD),
        .vss(0.0),

        .voutp(vinp),
        .voutn(vinp),

        .vinp(vinp),
        .vinn(vinn)
    );

    board_top #(
        .N_QUANTIZER_BITS(4)
    ) DUT (
        .vdd(VDD),

        .clk(i_clk_if.clk_driven),
        .arst_n(i_reset_if.bit_driven),

        .vinp(vinp),
        .vinn(vinn),

        .spi_signals(i_spi_if)
    );

    tb_top_cfg cfg;

    initial begin
        cfg = new("tb_top_cfg");
        cfg.vif_spi = i_spi_if;
        cfg.vif_reset = i_reset_if;
        cfg.vif_clk = i_clk_if;
        cfg.vif_adc = m_bridge.bridge_if;
        cfg.vproxy_adc = m_bridge.proxy;

        uvm_config_db #(tb_top_cfg)::set(null, "*", "tb_top_cfg", cfg);

        run_test("base_test");
    end

endmodule
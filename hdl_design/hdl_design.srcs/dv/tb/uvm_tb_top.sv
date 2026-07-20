`timescale 1ns/1ps

import uvm_pkg::*;
`include "uvm_macros.svh"

import base_test_pkg::*;
import tests_pkg::*;

/**
Module: uvm_tb_top

Toplevel static module. Instantiates the board as the DUT instead of the digital only,
with the board as a wrapper around digital.

Instantiates bridge and interfaces and runs the current test.
*/
module uvm_tb_top ();

    wire adc_csb;
    wire dac_csb;
    wire scl;
    wire mosi;
    wire miso;

    pulldown pd_scl (scl );
    pulldown pd_mosi(mosi);
    pulldown pd_miso(miso);

    bit_bus_if #(.WIDTH(1)) i_reset_if     ();
    oscillator_if           i_clk_if       ();
    spi_if i_dac_spi_if   (
        .csb (dac_csb),
        .scl (scl),
        .mosi(mosi),
        .miso(miso)
    );
    spi_if                  i_adc_spi_if   (
        .csb (adc_csb),
        .scl (scl),
        .mosi(mosi),
        .miso(miso)
    );

    assign i_clk_if.clk_observed = i_clk_if.clk_driven;
    assign i_reset_if.bit_observed = i_reset_if.bit_driven;

    status_if i_status_if ();

    tb_top_cfg cfg;

    chip_top DUT (
        // SPI interfaces
        .adc_csb,    
        .dac_csb,
        .scl,
        .miso,
        .mosi,

        // system clock
        .sysclk(i_clk_if.clk_driven),
        .arst_n(i_reset_if.bit_driven),

        // other signals, unused for now
        .sar_adc_in(0)
    );

    initial begin
        cfg = new("tb_top_cfg");
        cfg.vif_adc_spi = i_adc_spi_if;
        cfg.vif_dac_spi = i_dac_spi_if;
        cfg.vif_reset   = i_reset_if;
        cfg.vif_clk     = i_clk_if;
        cfg.vif_status  = i_status_if;

        uvm_config_db #(tb_top_cfg)::set(null, "*", "tb_top_cfg", cfg);

        run_test("reg_rw_test");
    end

endmodule
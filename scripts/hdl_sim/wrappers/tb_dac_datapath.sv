// Cocotb wrapper for the DAC datapath block test.
//
// rst_n is active-low. That matches dac_datapath. test_dac_top already
// synchronizes its arst_n into this same rst_n before the datapath.
//
// cocotb and Verilator cannot drive the unpacked PeakRDL hwif_out struct
// on the DUT boundary, so each software-visible field is a flat input
// here and is packed into dac_regs__out_t below. hwif_in is the hardware
// writeback (only STATUS.dsm_locked.next). The datapath ties that off.
//
// Two dac_5311 models convert the serial pins into real voltages.

module tb_dac_datapath (
    input logic clk,
    input logic rst_n,

    input logic [3:0]  amplitude_scale,
    input logic [3:0]  amplitude,
    input logic        dacp_enable,
    input logic        dacp_mode,
    input logic        dacn_enable,
    input logic        dacn_mode,
    input logic        dsm_enable,
    input logic [7:0]  dacp_dc_value,
    input logic [7:0]  dacn_dc_value,
    input logic [7:0]  clk_div_value,
    input logic [1:0]  dacp_power,
    input logic [1:0]  dacn_power,
    input logic [15:0] frequency,

    output real dacp_real,
    output real dacn_real
);

    dac_regs_mod_pkg::dac_regs__in_t  hwif_in;
    dac_regs_mod_pkg::dac_regs__out_t hwif_out;

    logic o_sclk;
    logic o_syncb_dacp;
    logic o_syncb_dacn;
    logic o_din_dacp;
    logic o_din_dacn;

    assign hwif_out.AC_CONFIG.amplitude_scale.value = amplitude_scale;
    assign hwif_out.AC_CONFIG.amplitude.value       = amplitude;
    assign hwif_out.ENABLE.dacp_enable.value        = dacp_enable;
    assign hwif_out.ENABLE.dacp_mode.value          = dacp_mode;
    assign hwif_out.ENABLE.dacn_enable.value        = dacn_enable;
    assign hwif_out.ENABLE.dacn_mode.value          = dacn_mode;
    assign hwif_out.ENABLE.dsm_enable.value         = dsm_enable;
    assign hwif_out.DACP_DC_VALUE.dc_value.value    = dacp_dc_value;
    assign hwif_out.DACN_DC_VALUE.dc_value.value    = dacn_dc_value;
    assign hwif_out.CLK_DIV.clk_div_value.value     = clk_div_value;
    assign hwif_out.STATUS.dacp_power.value         = dacp_power;
    assign hwif_out.STATUS.dacn_power.value         = dacn_power;
    assign hwif_out.FREQUENCY.frequency.value       = frequency;

    dac_datapath i_dac_datapath (
        .clk          (clk),
        .rst_n        (rst_n),
        .hwif_in      (hwif_in),
        .hwif_out     (hwif_out),
        .o_sclk       (o_sclk),
        .o_syncb_dacp (o_syncb_dacp),
        .o_syncb_dacn (o_syncb_dacn),
        .o_din_dacp   (o_din_dacp),
        .o_din_dacn   (o_din_dacn)
    );

    dac_5311 i_dacp (
        .syncb (o_syncb_dacp),
        .sclk  (o_sclk),
        .din   (o_din_dacp),
        .rst_n (rst_n),
        .vout  (dacp_real)
    );

    dac_5311 i_dacn (
        .syncb (o_syncb_dacn),
        .sclk  (o_sclk),
        .din   (o_din_dacn),
        .rst_n (rst_n),
        .vout  (dacn_real)
    );

    wire _unused_hwif = &{1'b0, hwif_in.STATUS.dsm_locked.next};

endmodule

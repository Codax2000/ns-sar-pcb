// Module: dac_datapath
// Structural skeleton of the sine-generator datapath.
//
// hwif_in / hwif_out are the PeakRDL structs from dac_regs_mod_pkg.
// hwif_out is the regblock output (software-programmed fields).
// hwif_in is the regblock input (hardware writeback). The only field
// today is STATUS.dsm_locked.next, held at 0.
//
// dacp_value and dacn_value are the unsigned 8-bit DAC5311 codes,
// same names as the generate_dac_values columns. They are 0 in reset
// and midscale (128) otherwise. The instantiated blocks do not
// compute them yet.

module dac_datapath (
    input  logic clk,
    input  logic rst_n,

    output dac_regs_mod_pkg::dac_regs__in_t  hwif_in,
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    output logic [7:0] dacp_value,
    output logic [7:0] dacn_value
);

    // Unsigned zero of generate_dac_values (signed code + 128).
    localparam logic [7:0] DAC_MIDSCALE = 8'h80;

    logic [15:0] phase;
    logic        phase_valid;
    logic [15:0] cosine;
    logic        cosine_valid;
    logic [15:0] cosine_dsm;
    logic        dsm_valid;

    phase_accumulator i_phase_accumulator (
        .rst_n    (rst_n),
        .clk      (clk),
        .hwif_out (hwif_out),
        .o_phase  (phase),
        .o_valid  (phase_valid)
    );

    cordic i_cordic (
        .rst_n    (rst_n),
        .clk      (clk),
        .hwif_out (hwif_out),
        .i_phase  (phase),
        .i_valid  (phase_valid),
        .o_cosine (cosine),
        .o_valid  (cosine_valid)
    );

    dsm_error_feedback i_dsm_error_feedback (
        .rst_n        (rst_n),
        .clk          (clk),
        .hwif_out     (hwif_out),
        .i_cosine     (cosine),
        .i_valid      (cosine_valid),
        .o_cosine_dsm (cosine_dsm),
        .o_valid      (dsm_valid)
    );

    dac5311_ctrl i_dac5311_ctrl (
        .rst_n        (rst_n),
        .clk          (clk),
        .hwif_out     (hwif_out),
        .i_cosine     (cosine),
        .i_cosine_dsm (cosine_dsm),
        .i_valid      (dsm_valid),
        .o_sclk       (),
        .o_syncb_dacp (),
        .o_syncb_dacn (),
        .o_din_dacp   (),
        .o_din_dacn   ()
    );

    // TODO: drive this from the delta-sigma warmup, not a constant.
    assign hwif_in.STATUS.dsm_locked.next = 1'b0;

    assign dacp_value = rst_n ? DAC_MIDSCALE : '0;
    assign dacn_value = rst_n ? DAC_MIDSCALE : '0;

endmodule

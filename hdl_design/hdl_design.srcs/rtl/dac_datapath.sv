// Module: dac_datapath
// Structural skeleton of the sine-generator datapath.
//
// hwif_out is the regblock output (software-programmed fields).
// hwif_in is the regblock input. The only field today is
// STATUS.dsm_locked.next, held at 0.
//
// Chain: phase accumulator -> CORDIC -> DSM -> bypass mux -> DAC5311
// control. Any software write ORs the writable fields' swmod strobes
// and resets that chain for one cycle (dp_rst_n). The block's own
// rst_n is what clears that strobe flop. The 8-bit codes never leave
// this hierarchy.
// One SCLK, a separate active-low SYNC and DIN for each DAC5311.
// test_dac_top maps these onto the board pins (separate SYNCb per DAC).

module dac_datapath (
    input  logic clk,
    input  logic rst,

    output dac_regs_mod_pkg::dac_regs__in_t  hwif_in,
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    output logic o_sclk,
    output logic o_syncb_dacp,
    output logic o_syncb_dacn,
    output logic o_din_dacp,
    output logic o_din_dacn
);

    logic               phase_en;
    logic signed [15:0] phase;
    logic               phase_valid;
    logic signed [15:0] sine;
    logic               sine_valid;
    logic signed  [7:0] sine_dsm;
    logic               dsm_valid;
    logic         [7:0] sine_to_dac;
    logic               dac_valid;

    // One-cycle datapath reset after a software write using RDL swmod (write)
    logic reg_write;
    logic reg_write_q;
    logic datapath_rst;
    logic dsm_locked;

    assign reg_write = hwif_out.ENABLE.dacp_enable.swmod
                     | hwif_out.ENABLE.dacp_mode.swmod
                     | hwif_out.ENABLE.dacn_enable.swmod
                     | hwif_out.ENABLE.dacn_mode.swmod
                     | hwif_out.ENABLE.dsm_enable.swmod;

    always_ff @(posedge clk) begin
        if (rst)
            reg_write_q <= 1'b0;
        else
            reg_write_q <= reg_write;
    end

    assign datapath_rst = rst || reg_write_q;

    phase_accumulator u_phase_accumulator (
        .rst      (datapath_rst),
        .clk      (clk),
        .hwif_out (hwif_out),
        .o_phase  (phase),
        .o_valid  (phase_valid)
    );

    cordic u_cordic (
        .rst      (datapath_rst),
        .clk      (clk),
        .hwif_out (hwif_out),
        .i_phase  (phase),
        .i_valid  (phase_valid),
        .o_sine   (sine),
        .o_valid  (sine_valid)
    );

    dsm_error_feedback u_dsm_error_feedback (
        .rst          (datapath_rst),
        .clk          (clk),
        .hwif_out     (hwif_out),
        .i_sine       (sine),
        .i_valid      (sine_valid),
        .o_sine_dsm   (sine_dsm),
        .o_valid      (dsm_valid),
        .o_dsm_locked (dsm_locked)
    );

    bypass_mux u_bypass_mux (
        .rst            (datapath_rst),
        .clk            (clk),
        .hwif_out       (hwif_out),
        .i_sine         ({!sine[15], sine[14:8]}),
        .i_sine_valid   (sine_valid),
        .i_sine_dsm     (sine_dsm),
        .i_dsm_valid    (dsm_valid),
        .o_sine         (sine_to_dac),
        .o_valid        (dac_valid)
    );

    dac5311_ctrl u_dac5311_ctrl (
        .rst           (datapath_rst),
        .clk           (clk),
        .hwif_out      (hwif_out),
        .i_sine        (sine_to_dac),
        .i_sine_valid  (dac_valid),
        .o_sclk        (o_sclk),
        .o_syncb_dacp  (o_syncb_dacp),
        .o_syncb_dacn  (o_syncb_dacn),
        .o_din_dacp    (o_din_dacp),
        .o_din_dacn    (o_din_dacn)
    );

    // TODO: drive this from the delta-sigma warmup, not a constant.
    assign hwif_in.STATUS.dsm_locked.next = dsm_locked;

endmodule

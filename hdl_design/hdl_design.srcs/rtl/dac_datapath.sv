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
// test_dac_top maps these onto the board pins (one shared SYNC).

module dac_datapath (
    input  logic clk,
    input  logic rst_n,

    output dac_regs_mod_pkg::dac_regs__in_t  hwif_in,
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    output logic o_sclk,
    output logic o_syncb_dacp,
    output logic o_syncb_dacn,
    output logic o_din_dacp,
    output logic o_din_dacn
);

    logic        phase_en;
    logic [15:0] phase;
    logic        phase_valid;
    logic [15:0] cosine;
    logic        cosine_valid;
    logic [15:0] cosine_dsm;
    logic        dsm_valid;
    logic [15:0] cosine_to_dac;
    logic        dac_valid;

    // One-cycle datapath reset after a software write. swmod is the
    // regblock's write strobe. STATUS.dsm_locked is read-only; its
    // swmod is tied off inside the regblock and is not a write.
    logic reg_write;
    logic reg_write_q;
    logic dp_rst_n;

    assign reg_write = hwif_out.AC_CONFIG.amplitude_scale.swmod
                     | hwif_out.AC_CONFIG.amplitude.swmod
                     | hwif_out.ENABLE.dacp_enable.swmod
                     | hwif_out.ENABLE.dacp_mode.swmod
                     | hwif_out.ENABLE.dacn_enable.swmod
                     | hwif_out.ENABLE.dacn_mode.swmod
                     | hwif_out.ENABLE.dsm_enable.swmod
                     | hwif_out.DACP_DC_VALUE.dc_value.swmod
                     | hwif_out.DACN_DC_VALUE.dc_value.swmod
                     | hwif_out.CLK_DIV.clk_div_value.swmod
                     | hwif_out.STATUS.dacp_power.swmod
                     | hwif_out.STATUS.dacn_power.swmod
                     | hwif_out.FREQUENCY.frequency.swmod;

    always_ff @(posedge clk) begin
        if (!rst_n)
            reg_write_q <= 1'b0;
        else
            reg_write_q <= reg_write;
    end

    assign dp_rst_n = rst_n & ~reg_write_q;

    // Sketch enable into the NCO. Either DAC being enabled runs it.
    assign phase_en = hwif_out.ENABLE.dacp_enable.value
                    | hwif_out.ENABLE.dacn_enable.value;

    phase_accumulator i_phase_accumulator (
        .rst_n    (dp_rst_n),
        .clk      (clk),
        .hwif_out (hwif_out),
        .i_en     (phase_en),
        .o_phase  (phase),
        .o_valid  (phase_valid)
    );

    // cordic i_cordic (
    //     .rst_n    (dp_rst_n),
    //     .clk      (clk),
    //     .hwif_out (hwif_out),
    //     .i_phase  (phase),
    //     .i_valid  (phase_valid),
    //     .o_cosine (cosine),
    //     .o_valid  (cosine_valid)
    // );

    // dsm_error_feedback i_dsm_error_feedback (
    //     .rst_n        (dp_rst_n),
    //     .clk          (clk),
    //     .hwif_out     (hwif_out),
    //     .i_cosine     (cosine),
    //     .i_valid      (cosine_valid),
    //     .o_cosine_dsm (cosine_dsm),
    //     .o_valid      (dsm_valid)
    // );

    // dsm_bypass_mux i_dsm_bypass_mux (
    //     .rst_n          (dp_rst_n),
    //     .clk            (clk),
    //     .hwif_out       (hwif_out),
    //     .i_cosine       (cosine),
    //     .i_cosine_valid (cosine_valid),
    //     .i_cosine_dsm   (cosine_dsm),
    //     .i_dsm_valid    (dsm_valid),
    //     .o_cosine       (cosine_to_dac),
    //     .o_valid        (dac_valid)
    // );

    // dac5311_ctrl i_dac5311_ctrl (
    //     .rst_n         (dp_rst_n),
    //     .clk           (clk),
    //     .hwif_out      (hwif_out),
    //     .i_cosine      (cosine_to_dac),
    //     .i_valid       (dac_valid),
    //     .o_sclk        (o_sclk),
    //     .o_syncb_dacp  (o_syncb_dacp),
    //     .o_syncb_dacn  (o_syncb_dacn),
    //     .o_din_dacp    (o_din_dacp),
    //     .o_din_dacn    (o_din_dacn)
    // );

    // // TODO: drive this from the delta-sigma warmup, not a constant.
    // assign hwif_in.STATUS.dsm_locked.next = 1'b0;

endmodule

module dac5311_ctrl (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Sample selected by dsm_bypass_mux.
    input  [15:0] i_sine,
    input         i_sine_valid,

    // One SCLK. Each DAC5311 has its own active-low SYNC and DIN.
    // Both SYNC outputs stay high (inactive) until the serializer exists.
    output logic o_sclk,
    output logic o_syncb_dacp,
    output logic o_syncb_dacn,
    output logic o_din_dacp,
    output logic o_din_dacn
);



endmodule

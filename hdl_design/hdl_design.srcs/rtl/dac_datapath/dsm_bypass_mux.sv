module dsm_bypass_mux (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Bypass path (CORDIC cosine) and modulator path.
    input  [15:0] i_cosine,
    input         i_cosine_valid,
    input  [15:0] i_cosine_dsm,
    input         i_dsm_valid,

    output [15:0] o_cosine,
    output        o_valid
);

    // ENABLE.dsm_enable selects the DSM sample. Both samples are stubs.
    wire sel;

    assign sel      = hwif_out.ENABLE.dsm_enable.value;
    assign o_cosine = sel ? i_cosine_dsm : i_cosine;
    assign o_valid  = sel ? i_dsm_valid : i_cosine_valid;

    wire _unused_ok = &{1'b0, rst_n, clk};

endmodule

module cordic (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // phase inputs
    input  [15:0] i_phase,
    input         i_valid,

    // angle outputs
    output [15:0] o_cosine,
    output        o_valid
);

    // CORDIC rotation is not implemented.
    assign o_cosine = '0;
    assign o_valid  = 1'b0;

    wire _unused_ok = &{1'b0, rst_n, clk, i_valid, i_phase,
                        hwif_out.AC_CONFIG.amplitude_scale.value,
                        hwif_out.AC_CONFIG.amplitude.value};

endmodule

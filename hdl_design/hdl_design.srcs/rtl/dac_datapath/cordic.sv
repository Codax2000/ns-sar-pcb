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

endmodule

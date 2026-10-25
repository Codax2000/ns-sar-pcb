module dsm_error_feedback (
    input  logic rst_n,
    input  logic clk,

    // register inputs
    input  dac_regs_mod_pkg::dac_regs__in_t  hwif_in,

    // cosine inputs
    input  [15:0] i_cosine,
    output        i_valid,

    // cosine outputs
    output [15:0] o_cosine_dsm,
    output        o_valid
);

endmodule

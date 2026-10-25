module cordic (
    input  logic rst_n,
    input  logic clk,

    // register inputs
    input  dac_regs_mod_pkg::dac_regs__in_t  hwif_in,

    // phase inputs
    input  [15:0] i_phase,
    output        i_valid,

    // angle outputs
    output [15:0] o_cosine,
    output        o_valid
);

endmodule

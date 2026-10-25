module phase_accumulator (
    input  logic rst_n,
    input  logic clk,

    // register inputs
    input  dac_regs_mod_pkg::dac_regs__in_t  hwif_in,

    // phase outputs
    output [15:0] o_phase,
    output        o_valid
);

endmodule

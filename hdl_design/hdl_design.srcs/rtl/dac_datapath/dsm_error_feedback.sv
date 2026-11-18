module dsm_error_feedback (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // cosine inputs
    input  [15:0] i_cosine,
    input         i_valid,

    // cosine outputs
    output [15:0] o_cosine_dsm,
    output        o_valid
);

    // Error feedback around this block is not implemented.
    // dsm_enable is the mux select, not an input to the modulator stub.
    assign o_cosine_dsm = '0;
    assign o_valid      = 1'b0;

    wire _unused_ok = &{1'b0, rst_n, clk, i_valid, i_cosine,
                        hwif_out.CLK_DIV.clk_div_value.value};

endmodule

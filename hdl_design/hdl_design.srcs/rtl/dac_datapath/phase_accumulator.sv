module phase_accumulator (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // phase outputs
    output [15:0] o_phase,
    output        o_valid
);

    // Frequency tuning word is not accumulated yet.
    assign o_phase = '0;
    assign o_valid = 1'b0;

    wire _unused_ok = &{1'b0, rst_n, clk, hwif_out.FREQUENCY.frequency.value};

endmodule

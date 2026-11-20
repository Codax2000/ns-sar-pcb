module cordic (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // phase inputs
    input logic signed [15:0] i_phase,
    input logic               i_valid,

    // angle outputs
    output logic signed [15:0] o_cosine,
    output logic               o_valid
);

    logic signed [15:0] x_prerotate, y_prerotate, z_remaining;
    logic        [3:0]  iteration;
    logic               prerotate_valid;
    logic               flip_x, pos_y, neg_y;

    cordic_glue_logic u_glue_logic (
        .rst(rst),
        .clk(clk),
        .i_phase(i_phase),
        .i_valid(i_valid),
        .o_phase_remaining(z_remaining),
        .o_flip_x(flip_x),
        .o_pos_y(pos_y),
        .o_neg_y(neg_y),
        .o_valid(prerotate_valid)
    );

endmodule

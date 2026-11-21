module cordic_glue_logic (
    input  logic               rst,
    input  logic               clk,

    input  logic signed [15:0] i_phase,
    input  logic               i_valid,

    output logic signed [15:0] o_phase_remaining,
    output logic        [1:0]  o_quadrant,
    output logic               o_valid
);

    wire signed  [15:0] remaining_phase = i_phase & 16'h3FFF;
    wire         [1:0]  quadrant = i_phase[15:14];

    always_ff @(posedge clk) begin : valid_reg_ungated
        if (rst) begin
            o_valid <= 0;
        end else begin
            if (i_valid) begin
                o_valid <= 1;
            end else begin
                o_valid <= 0;
            end
        end
    end : valid_reg_ungated

    always_ff @(posedge clk) begin : output_reg_gated
        if (rst) begin
            o_phase_remaining <= 0;
            o_quadrant <= 2'h0;
        end else begin
            if (i_valid) begin
                o_phase_remaining <= remaining_phase;
                o_quadrant <= quadrant;
            end
        end
    end : output_reg_gated

endmodule
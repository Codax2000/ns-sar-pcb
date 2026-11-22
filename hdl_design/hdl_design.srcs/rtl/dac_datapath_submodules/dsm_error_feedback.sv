module dsm_error_feedback (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // cosine inputs
    input  [15:0] i_sine,
    input         i_valid,

    // cosine outputs
    output  [7:0] o_sine_dsm,
    output        o_valid
);

    logic               dsm_enable;
    logic signed [15:0] sine_sum;
    logic signed [7:0]  dsm_error_r, dsm_error_rr;
    wire  signed [8:0]  dsm_error_x2 = dsm_error_r << 1;
    wire  signed [7:0]  dsm_error = sine_sum[7:0];

    assign dsm_enable = hwif_out.ENABLE.dsm_enable.value;

    always_ff @(posedge clk) begin : dsm_error_feedback_logic
        if (rst) begin
            dsm_error_r <= 0;
            dsm_error_rr <= 0;
        end
        else begin

            if (i_valid && dsm_enable) begin
                sine_sum <= 16'(dsm_error_x2) + 16'(dsm_error_rr) + i_sine;
                dsm_error_r  <=  dsm_error;
                dsm_error_rr <= -dsm_error_r;
            end
        end
    end : dsm_error_feedback_logic

    always_ff @(posedge clk) begin : dsm_error_feedback_output_logic
        if (rst) begin
            o_sine_dsm <= 0;
            o_valid <= 0;
        end
        else begin
            if (i_valid && dsm_enable) begin
                o_sine_dsm <= {!sine_sum[15], sine_sum[14:8]};
                o_valid <= 1;
            end
            else begin
                o_valid <= 0;
            end
        end
    end : dsm_error_feedback_output_logic

endmodule

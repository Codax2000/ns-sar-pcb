module dsm_error_feedback (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // cosine inputs (signed Q1.15 from CORDIC)
    input  logic signed [15:0] i_sine,
    input                      i_valid,

    // cosine outputs (unsigned offset-binary for the DAC)
    output logic [7:0] o_sine_dsm,
    output logic       o_valid,

    output logic       o_dsm_locked
);

    parameter int DSM_WARMUP_COUNT = 1000;
    localparam int DSM_COUNT_W = $clog2(DSM_WARMUP_COUNT) + 1;

    // Match models.sinegen_dac._modulate_dsm:
    //   acc      = sample + older + 2*previous
    //   q        = sat(acc >>> 8, -128..127)
    //   error    = (q << 8) - acc
    //   previous = -error   (next)
    //   older    = error_prev = -previous (next)
    logic signed [16:0] previous_r;
    logic signed [16:0] older_r;

    wire signed [17:0] acc =
        18'(i_sine) + 18'(older_r) + (18'(previous_r) <<< 1);

    wire signed [17:0] q_ext = acc >>> 8;
    logic signed [7:0] q;
    always_comb begin
        if (q_ext > 18'sd127)
            q = 8'sd127;
        else if (q_ext < -18'sd128)
            q = -8'sd128;
        else
            q = q_ext[7:0];
    end

    wire signed [17:0] error = (18'(q) <<< 8) - acc;

    logic [DSM_COUNT_W-1:0] dsm_count;
    localparam logic [DSM_COUNT_W-1:0] DSM_WARMUP_THRESHOLD =
        DSM_COUNT_W'(DSM_WARMUP_COUNT);

    wire dsm_enable = hwif_out.ENABLE.dsm_enable.value;

    always_ff @(posedge clk) begin : dsm_error_feedback_logic
        if (rst) begin
            previous_r  <= '0;
            older_r     <= '0;
            dsm_count   <= '0;
            o_dsm_locked <= 1'b0;
            o_sine_dsm  <= 8'h00;
            o_valid     <= 1'b0;
        end
        else if (i_valid && dsm_enable) begin
            // Same-cycle quantize of acc that includes i_sine.
            o_sine_dsm <= {!q[7], q[6:0]};
            o_valid    <= 1'b1;
            previous_r <= 17'(-error);
            older_r    <= 17'(-previous_r);
            if (dsm_count < DSM_WARMUP_THRESHOLD)
                dsm_count <= dsm_count + 1'b1;
            else
                o_dsm_locked <= 1'b1;
        end
        else begin
            o_valid <= 1'b0;
        end
    end : dsm_error_feedback_logic

endmodule

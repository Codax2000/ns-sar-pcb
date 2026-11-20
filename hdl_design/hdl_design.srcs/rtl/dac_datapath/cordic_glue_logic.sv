module cordic_glue_logic (
    input  logic               rst,
    input  logic               clk,

    input  logic signed [15:0] i_phase,
    input  logic               i_valid,

    output logic signed [15:0] o_phase_remaining,
    output logic               o_flip_x,
    output logic               o_pos_y,
    output logic               o_neg_y,
    output logic               o_valid
);

    typedef enum logic [1:0] {
        QUADRANT_0 = 0,
        QUADRANT_1 = 1,
        QUADRANT_2 = 2,
        QUADRANT_3 = 3
    } quadrant_t;

    logic signed [15:0] remaining_phase;
    logic               o_flip_x_n, o_pos_y_n, o_neg_y_n;
    quadrant_t          quadrant;

    assign quadrant = quadrant_t'(i_phase[15:14]);
    assign remaining_phase = i_phase & 16'h3FFF;

    always_comb begin
        case (quadrant)
            QUADRANT_0: begin
                o_flip_x_n = 0;
                o_pos_y_n = 0;
                o_neg_y_n = 0;
            end
            QUADRANT_1: begin
                o_flip_x_n = 0;
                o_pos_y_n = 1;
                o_neg_y_n = 0;
            end
            QUADRANT_2: begin
                o_flip_x_n = 1;
                o_pos_y_n = 0;
                o_neg_y_n = 0;
            end
            QUADRANT_3: begin
                o_flip_x_n = 1;
                o_pos_y_n = 0;
                o_neg_y_n = 1;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            o_valid <= 0;
        end else begin
            if (i_valid) begin
                o_valid <= 1;
            end else begin
                o_valid <= 0;
            end
        end
    end

    always_ff @(posedge clk) begin : output_reg_gated
        if (rst) begin
            o_phase_remaining <= 0;
            o_flip_x <= 0;
            o_pos_y <= 0;
            o_neg_y <= 0;
        end else begin
            if (i_valid) begin
                o_phase_remaining <= remaining_phase;
                o_flip_x <= o_flip_x_n;
                o_pos_y <= o_pos_y_n;
                o_neg_y <= o_neg_y_n;
            end
        end
    end : output_reg_gated

endmodule
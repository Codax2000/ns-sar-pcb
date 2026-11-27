module cordic (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // phase inputs
    input logic signed [15:0] i_phase,
    input logic               i_valid,

    // angle outputs
    output logic signed [15:0] o_sine,
    output logic               o_valid
);

    localparam logic [3:0] ITERATION_MAX = 4'hF;

    localparam logic [15:0] FULLSCALE_SHIFT1 = 16'h52E7 >> 1;
    localparam logic [15:0] FULLSCALE_SHIFT2 = 16'h52E7 >> 2;
    localparam logic [15:0] FULLSCALE_SHIFT3 = 16'h52E7 >> 3;
    localparam logic [15:0] FULLSCALE_SHIFT4 = 16'h52E7 >> 4;

    logic             [2:0]  magnitude_sum_counter;
    logic signed [3:0][15:0] magnitude_shift;
    logic signed      [15:0] magnitude_shift_12, magnitude_shift_34, magnitude;
    logic                    quadrant_valid;
    logic             [1:0]  quadrant;
    logic signed      [15:0] x_prerotate_n, y_prerotate_n;
    logic signed      [15:0] x_prerotate, y_prerotate, z_remaining;
    logic                    prerotate_valid;
    logic             [3:0]  iteration, iteration_r, iteration_rr;
    logic                    cordic_mem_read_en;
    logic signed      [15:0] atan_rom_data;
    logic                    iteration_valid;
    logic signed      [15:0] x_cordic, y_cordic, z_remaining_cordic;
    logic signed      [15:0] x_shifted, y_shifted;
    logic                    direction;

    cordic_glue_logic u_glue_logic (
        .rst(rst),
        .clk(clk),
        .i_phase(i_phase),
        .i_valid(i_valid),
        .o_phase_remaining(z_remaining),
        .o_quadrant(quadrant),
        .o_valid(quadrant_valid)
    );

    assign magnitude_shift[0] = hwif_out.AC_CONFIG.amplitude_div_linear.value[0] ? FULLSCALE_SHIFT4 : 16'h0000;
    assign magnitude_shift[1] = hwif_out.AC_CONFIG.amplitude_div_linear.value[1] ? FULLSCALE_SHIFT3 : 16'h0000;
    assign magnitude_shift[2] = hwif_out.AC_CONFIG.amplitude_div_linear.value[2] ? FULLSCALE_SHIFT2 : 16'h0000;
    assign magnitude_shift[3] = hwif_out.AC_CONFIG.amplitude_div_linear.value[3] ? FULLSCALE_SHIFT1 : 16'h0000;

    // amplitude scaling
    always_ff @(posedge clk) begin : magnitude_sum_shifter
        if (rst) begin
            magnitude_sum_counter <= 3'b001;
        end
        else begin
            magnitude_sum_counter <= magnitude_sum_counter << 1;
        end
    end : magnitude_sum_shifter

    always_ff @(posedge clk) begin : magnitude_sum_adder_tree
        if (rst) begin
            magnitude_shift_12 <= 16'h0000;
            magnitude_shift_34 <= 16'h0000;
            magnitude          <= 16'h0000;
        end
        else begin
            if (magnitude_sum_counter[1]) begin
                magnitude_shift_12 <= magnitude_shift[0] + magnitude_shift[1];
                magnitude_shift_34 <= magnitude_shift[2] + magnitude_shift[3];
            end
            else if (magnitude_sum_counter[2]) begin
                magnitude          <= magnitude_shift_12 + magnitude_shift_34;
            end
        end
    end : magnitude_sum_adder_tree

    always_comb begin : prerotate_logic
        case (quadrant)
            2'h0: begin
                x_prerotate_n = magnitude;
                y_prerotate_n = 16'h0000;
            end
            2'h1: begin
                x_prerotate_n = 16'h0000;
                y_prerotate_n = magnitude;
            end
            2'h2: begin
                x_prerotate_n = -magnitude;
                y_prerotate_n = 16'h0000;
            end
            2'h3: begin
                x_prerotate_n = 16'h0000;
                y_prerotate_n = -magnitude;
            end
        endcase
    end : prerotate_logic

    always_ff @(posedge clk) begin : prerotate_reg
        if (rst) begin
            x_prerotate <= 16'h0000;
            y_prerotate <= 16'h0000;
            prerotate_valid <= 0;
        end
        else begin
            if (quadrant_valid) begin
                x_prerotate <= x_prerotate_n;
                y_prerotate <= y_prerotate_n;
                prerotate_valid <= 1;
            end
            else begin
                prerotate_valid <= 0;
            end
        end
    end : prerotate_reg

    always_ff @(posedge clk) begin : cordic_iteration
        if (rst) begin
            iteration <= 4'h0;
            iteration_r <= 4'h0;
            iteration_rr <= 4'h0;
            cordic_mem_read_en <= 0;
            iteration_valid <= 0;
        end
        else begin
            iteration_valid <= cordic_mem_read_en;
            iteration_r <= iteration;
            iteration_rr <= iteration_r;
            if (quadrant_valid) begin
                cordic_mem_read_en <= 1;
                iteration <= 4'h0;
            end
            else if (iteration == ITERATION_MAX) begin
                cordic_mem_read_en <= 0;
                iteration <= 4'h0;
            end
            else if (cordic_mem_read_en) begin
                iteration <= iteration + 4'h1;
            end
        end
    end : cordic_iteration

    atan_rom u_atan_rom (
        .clk(clk),
        .rst(rst),
        .rd_en(cordic_mem_read_en),
        .addr(iteration),
        .data(atan_rom_data)
    );

    assign x_shifted = x_cordic >>> iteration_r;
    assign y_shifted = y_cordic >>> iteration_r;

    always_ff @(posedge clk) begin : cordic_iteration_logic
        if (rst) begin
            x_cordic <= 16'h0000;
            y_cordic <= 16'h0000;
            z_remaining_cordic <= 16'h0000;
            direction <= 0;
        end
        else begin
            if (prerotate_valid) begin
                z_remaining_cordic <= z_remaining;
                x_cordic  <= x_prerotate;
                y_cordic  <= y_prerotate;
                direction <= z_remaining >= 0;
            end
            else if (iteration_valid) begin
                x_cordic <= direction ? x_cordic - y_shifted : x_cordic + y_shifted;
                y_cordic <= direction ? y_cordic + x_shifted : y_cordic - x_shifted;
                z_remaining_cordic <= direction ? z_remaining_cordic - atan_rom_data : z_remaining_cordic + atan_rom_data;
                direction          <= direction ? (z_remaining_cordic - atan_rom_data) >= 0 : (z_remaining_cordic + atan_rom_data) >= 0;
            end
        end
    end : cordic_iteration_logic

    always_ff @(posedge clk) begin : output_reg
        if (rst) begin
            o_sine <= 16'h0000;
            o_valid <= 0;
        end
        else begin
            if (iteration_rr == ITERATION_MAX) begin
                o_sine <= y_cordic >>> (4'hF - hwif_out.AC_CONFIG.amplitude_div_log.value);
                o_valid <= 1;
            end
            else begin
                o_valid <= 0;
            end
        end
    end : output_reg

endmodule

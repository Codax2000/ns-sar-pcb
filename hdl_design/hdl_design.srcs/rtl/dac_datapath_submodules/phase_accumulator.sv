module phase_accumulator (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // phase outputs
    output [15:0] o_phase,
    output        o_valid
);

    localparam  VALID_COUNT = 34;
    logic [7:0] idle_counter;

    wire dacp_ac_en = hwif_out.ENABLE.dacp_enable.value &&
                        (hwif_out.ENABLE.dacp_mode.value == dac_regs_mod_pkg::dac_regs__frequency_mode_e__AC);
    wire dacn_ac_en = hwif_out.ENABLE.dacn_enable.value &&
                        (hwif_out.ENABLE.dacn_mode.value == dac_regs_mod_pkg::dac_regs__frequency_mode_e__AC);
    wire phase_increment_gt0 = hwif_out.FREQUENCY.frequency.value != 16'h0000;
    wire accumulator_en = (dacp_ac_en || dacn_ac_en) && phase_increment_gt0;

    always_ff @(posedge clk) begin
        if (rst) begin
            idle_counter <= 8'h00;
            o_phase <= 16'h0000;
            o_valid <= 1'b0;
        end
        else if (accumulator_en) begin
            if (idle_counter == VALID_COUNT - 1) begin
                idle_counter <= 8'h00;
                o_valid <= 1'b1;
                o_phase <= o_phase + hwif_out.FREQUENCY.frequency.value;
            end
            else begin
                o_valid <= 1'b0;
                idle_counter <= idle_counter + 1;
            end
        end
    end

endmodule

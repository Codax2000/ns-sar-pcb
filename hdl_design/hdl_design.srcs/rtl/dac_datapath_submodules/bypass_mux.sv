module bypass_mux #(
    parameter WIDTH = 8
) (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Bypass path (CORDIC) and modulator path. Per-DAC AC enable is
    // handled downstream in dac5311_ctrl.
    input  logic [WIDTH-1:0] i_sine,
    input  logic             i_sine_valid,
    input  logic [WIDTH-1:0] i_sine_dsm,
    input  logic             i_dsm_valid,

    output logic [WIDTH-1:0] o_sine,
    output logic             o_valid
);

    always_ff @(posedge clk) begin : dsm_bypass
        if (rst) begin
            o_sine  <= '0;
            o_valid <= 1'b0;
        end else begin
            if (hwif_out.ENABLE.dsm_enable.value && i_dsm_valid) begin
                o_sine  <= i_sine_dsm;
                o_valid <= 1'b1;
            end
            else if (!hwif_out.ENABLE.dsm_enable.value && i_sine_valid) begin
                o_sine  <= i_sine;
                o_valid <= 1'b1;
            end
            else begin
                o_valid <= 1'b0;
            end
        end
    end : dsm_bypass

endmodule

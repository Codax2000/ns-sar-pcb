module bypass_mux #(
    parameter WIDTH = 8
) (
    input  logic rst,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Bypass path (CORDIC cosine) and modulator path.
    input  [WIDTH-1:0] i_sine,
    input              i_sine_valid,
    input  [WIDTH-1:0] i_sine_dsm,
    input              i_dsm_valid,

    output [WIDTH-1:0] o_dacp,
    output [WIDTH-1:0] o_dacn,
    output             o_dacp_valid,
    output             o_dacn_valid
);

    logic [WIDTH-1:0] dac_ac;
    logic             ac_valid;

    wire dacp_ac_enabled = hwif_out.ENABLE.dacp_ac_enable.value && hwif_out.ENABLE.dacp_enable.value;
    wire dacn_ac_enabled = hwif_out.ENABLE.dacn_ac_enable.value && hwif_out.ENABLE.dacn_enable.value;

    always_ff @(posedge clk) begin : dsm_bypass
        if (rst) begin
            dac_ac <= 0;
            ac_valid <= 1'b0;
        end else begin
            if (hwif_out.ENABLE.dsm_enable.value == 1'b1 && i_dsm_valid == 1'b1) begin
                dac_ac <= i_sine_dsm;
                ac_valid <= 1'b1;
            end
            else if (hwif_out.ENABLE.dsm_enable.value == 1'b0 && i_sine_valid == 1'b1) begin
                dac_ac <= i_sine;
                ac_valid <= 1'b1;
            end
            else begin
                ac_valid <= 1'b0;
            end
        end
    end : dsm_bypass

    always_ff @(posedge clk) begin : dacp_output
        if (rst) begin
            o_dacp <= 0;
            o_dacp_valid <= 1'b0;
        end else begin
            if (dacp_ac_enabled && ac_valid) begin
                o_dacp <= dac_ac;
                o_dacp_valid <= 1'b1;
            end
            else begin
                o_dacp_valid <= 1'b0;
            end
        end
    end : dacp_output

    always_ff @(posedge clk) begin : dacn_output
        if (rst) begin
            o_dacn <= 0;
            o_dacn_valid <= 1'b0;
        end else begin
            if (dacp_ac_enabled && ac_valid) begin
                o_dacn <= dac_ac;
                o_dacn_valid <= 1'b1;
            end
            else begin
                o_dacn_valid <= 1'b0;
            end
        end
    end : dacp_output
    
endmodule

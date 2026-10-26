module dac5311_ctrl (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Sample selected by dsm_bypass_mux.
    input  [15:0] i_cosine,
    input         i_valid,

    // One SCLK. Each DAC5311 has its own active-low SYNC and DIN.
    // Both SYNC outputs stay high (inactive) until the serializer exists.
    output logic o_sclk,
    output logic o_syncb_dacp,
    output logic o_syncb_dacn,
    output logic o_din_dacp,
    output logic o_din_dacn
);

    // Serializer is not implemented. 8-bit codes stay inside this block.
    assign o_sclk       = 1'b0;
    assign o_syncb_dacp = 1'b1;
    assign o_syncb_dacn = 1'b1;
    assign o_din_dacp   = 1'b0;
    assign o_din_dacn   = 1'b0;

    wire _unused_ok = &{1'b0, rst_n, clk, i_valid, i_cosine,
                        hwif_out.ENABLE.dacp_enable.value,
                        hwif_out.ENABLE.dacn_enable.value,
                        hwif_out.ENABLE.dacp_mode.value,
                        hwif_out.ENABLE.dacn_mode.value,
                        hwif_out.DACP_DC_VALUE.dc_value.value,
                        hwif_out.DACN_DC_VALUE.dc_value.value,
                        hwif_out.STATUS.dacp_power.value,
                        hwif_out.STATUS.dacn_power.value,
                        hwif_out.CLK_DIV.clk_div_value.value};

endmodule

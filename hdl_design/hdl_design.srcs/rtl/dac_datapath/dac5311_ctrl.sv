module dac5311_ctrl (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // Sample selected by dsm_bypass_mux.
    input  [15:0] i_cosine,
    input         i_valid,

    // Board pins for the two DAC5311s. One SYNC and one SCLK are
    // shared. syncb is active-low and is held high.
    output sinegen_syncb,
    output sinegen_sclk,
    output sinegen_dinp,
    output sinegen_dinn
);

    // Serializer is not implemented. 8-bit codes stay inside this block.
    assign sinegen_syncb = 1'b1;
    assign sinegen_sclk  = 1'b0;
    assign sinegen_dinp  = 1'b0;
    assign sinegen_dinn  = 1'b0;

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

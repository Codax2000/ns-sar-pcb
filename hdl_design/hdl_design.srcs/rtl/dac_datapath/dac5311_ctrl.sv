module dac5311_ctrl (
    input  logic rst_n,
    input  logic clk,

    // Software-programmed dac_regs fields (regblock hwif_out).
    input  dac_regs_mod_pkg::dac_regs__out_t hwif_out,

    // cosine inputs
    input  [15:0] i_cosine,
    input  [15:0] i_cosine_dsm,
    input         i_valid,

    // DAC5311 serial pins. syncb is active-low and is held high.
    output        o_sclk,
    output        o_syncb_dacp,
    output        o_syncb_dacn,
    output        o_din_dacp,
    output        o_din_dacn
);

    // Serializer is not implemented.
    assign o_sclk       = 1'b0;
    assign o_syncb_dacp = 1'b1;
    assign o_syncb_dacn = 1'b1;
    assign o_din_dacp   = 1'b0;
    assign o_din_dacn   = 1'b0;

    wire _unused_ok = &{1'b0, rst_n, clk, i_valid, i_cosine, i_cosine_dsm,
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

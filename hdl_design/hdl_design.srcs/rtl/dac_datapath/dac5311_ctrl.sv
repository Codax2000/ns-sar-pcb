module dac5311_ctrl (
    input  logic rst_n,
    input  logic clk,

    // register inputs
    input  dac_regs_mod_pkg::dac_regs__in_t  hwif_in,

    // phase inputs
    input  [15:0] i_cosine,
    input  [15:0] i_cosine_dsm,
    output        i_valid,

    // DAC output control
    output        o_sclk,
    output        o_syncb_dacp,
    output        o_syncb_dacn,
    output        o_din_dacp,
    output        o_din_dacn,
);

endmodule

module dig_core #(
    parameter N_SAR_BITS = 3,
    parameter N_SYNC_STAGES = 3,

    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 15
) (
    // clkgen pins
    input logic i_sysclk,
    input logic i_sysrst_b,
    
    // analog boundary pins
    input logic i_sar_compare,

    // SPI IO pins
    input logic i_cs_b,
    input logic i_scl,
    input logic i_mosi,
    output logic o_miso
);

    // system signals from clock gen and reset IP
    logic pll_clk;
    logic pll_is_locked;
    logic sys_rst_b;
    logic sys_rst;
    
    spi #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) i_spi (
        .scl(i_scl),
        .mosi(i_mosi),
        .miso(o_miso),
        .cs_b(i_cs_b || (!sys_rst_b)) // hold SPI in reset if the device is in reset

    );

    assign spi_rd_data = 0;

    clk_gen_xip i_clk_gen (
        .reset(sys_rst),
        .clk_in1(i_sysclk),
        .clk_out1(pll_clk),
        .locked(pll_is_locked)
    );

    reset_gen_xip i_reset_gen (
        .slowest_sync_clk(i_sysclk),
        .ext_reset_in(i_sysrst_b),

        .dcm_locked(1'b1),
        .aux_reset_in(1'b1),
        .mb_debug_sys_rst(1'b0),

        .peripheral_reset(sys_rst)
    );

    assign sys_rst_b = (!sys_rst) && pll_is_locked;

endmodule
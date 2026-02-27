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


    // Group: CPUIF Interface Signals. No ACKs, not useful.
    logic        if_req;
    logic        if_rd_en;
    logic [15:0] if_addr;
    logic  [7:0] if_wr_data;

    logic  [7:0] if_rd_data;
    logic        if_rd_err;
    logic        if_wr_err;

    spi #(
        .ADDR_BYTES(2)
    ) i_spi (
        .scl(i_scl),
        .mosi(i_mosi),
        .miso(o_miso),
        .cs_b(i_cs_b),

        .if_req,
        .if_rd_en,
        .if_addr,
        .if_wr_data,

        .if_rd_data,
        .if_rd_err,
        .if_wr_err
    );

    adc_regs_mod_pkg::adc_regs__in_t hwif_in_spiclk;
    adc_regs_mod_pkg::adc_regs__out_t hwif_out_spiclk;

    logic por_reset;
    initial begin
        por_reset = 1;
        repeat (2) @(negedge i_scl);
        por_reset = 0;
    end

    adc_regs_mod i_registers (
        .clk(!i_scl),
        .rst(por_reset),

        .s_cpuif_req(if_req),
        .s_cpuif_req_is_wr(!if_rd_en),
        .s_cpuif_addr(if_addr),
        .s_cpuif_wr_data(if_wr_data),
        .s_cpuif_wr_biten(8'hFF),
        .s_cpuif_rd_err(if_rd_err),
        .s_cpuif_rd_data(if_rd_data),
        .s_cpuif_wr_err(if_wr_err),

        .hwif_in(hwif_in_spiclk),
        .hwif_out(hwif_out_spiclk)
    );

    // Group: clocking signals & PLL
    logic pll_clk;
    assign pll_clk = i_sysclk;

    adc_regs_mod_pkg::adc_regs__in_t hwif_in_sysclk;
    adc_regs_mod_pkg::adc_regs__out_t hwif_out_sysclk;

    assign hwif_in_spiclk.ADC_CTRL.START_CONVERSION.hwclr = 0;
    assign hwif_in_sysclk.ADC_CTRL.SYNC_RESET_RB.next = 0;
    assign hwif_in_sysclk.ADC_CTRL.MAIN_STATE_RB.next[3:0] = 0;
    assign hwif_in_sysclk.CONVERSION_FLAGS.N_VALID_SAMPLES.next[14:0] = 0;
    assign hwif_in_sysclk.CONVERSION_FLAGS.PREVIOUS_CONVERSION_CORRUPTED.next = 0;
    assign hwif_in_sysclk.adc_output_mem.rd_ack = 0;
    assign hwif_in_sysclk.adc_output_mem.rd_data[7:0] = 0;
    assign hwif_in_sysclk.adc_output_mem.wr_ack = 0;

    adc_regs_reg_sync i_sync (
        .hwif_in_sysclk(hwif_in_sysclk),
        .hwif_in_ifclk(hwif_in_spiclk),
        .hwif_out_sysclk(hwif_out_sysclk),
        .hwif_out_ifclk(hwif_out_spiclk),
        .sysclk(pll_clk),
        .ifclk(!i_scl),
        .sysclk_rst(por_reset),
        .ifclk_rst(i_cs_b) // TODO: sync this signal to SPI clk
    );

endmodule

module adc_top (
    // system clock and reset
    input sysclk,
    input arst_n,
    
    // SPI interface    
    input  logic csb,
    input  logic scl,
    input  logic mosi,
    output logic miso,
    output logic miso_en
);

    // Sync reset generation
    logic rst_n;

    sync_nstage #(.N_BITS(1)) i_rst_sync (
        .src_data(arst_n),
        .dest_data(rst_n),
        .src_clk(1'b0),
        .dest_clk(sysclk),
        .dest_clk_rst(1'b0)
    );

    // Register interface
    logic adc_if_req;
    logic adc_if_rd_en;
    logic adc_if_addr;
    logic adc_if_wr_data;
    logic adc_if_rd_data;
    logic adc_if_rd_err;
    logic adc_if_wr_err;

    spi i_dac_spi (
        .sysclk(sysclk),
        .rst_n (rst_n),

        .scl    (scl),
        .mosi   (mosi),
        .cs_b   (csb),
        .miso   (miso),
        .miso_en(miso_en),

        .if_req    (adc_if_req   ),
        .if_rd_en  (adc_if_rd_en ),
        .if_addr   (adc_if_addr  ),
        .if_wr_data(adc_if_wr_dat),
        .if_rd_data(adc_if_rd_dat),
        .if_rd_err (adc_if_rd_err),
        .if_wr_err (adc_if_wr_err)
    );

    adc_regs_mod_pkg::adc_regs__in_t  hwif_in;
    adc_regs_mod_pkg::adc_regs__out_t hwif_out;

    adc_regs_mod i_registers (
        .clk(!i_scl),
        .rst(rst_spi),

        .s_cpuif_req(adc_if_req),
        .s_cpuif_req_is_wr(!adc_if_rd_en),
        .s_cpuif_addr(adc_if_addr),
        .s_cpuif_wr_data(adc_if_wr_data),
        .s_cpuif_wr_biten(16'hFFFF),
        .s_cpuif_rd_err(adc_if_rd_err),
        .s_cpuif_rd_data(adc_if_rd_data),
        .s_cpuif_wr_err(adc_if_wr_err),

        .hwif_in(hwif_in),
        .hwif_out(hwif_out)
    );

    // TODO: update these once more of the design is done
    assign hwif_in.ADC_OUTPUT_MEM.rd_ack = 0;
    assign hwif_in.ADC_OUTPUT_MEM.rd_data = 0;
    assign hwif_in.ADC_OUTPUT_MEM.wr_ack = 0;
    assign hwif_in.ADC_CTRL.START_CONVERSION.hwclr = 0;
    assign hwif_in.ADC_CTRL.SYNC_RESET_RB.next = 0;
    assign hwif_in.ADC_CTRL.MAIN_STATE_RB.next = 0;
    assign hwif_in.CONVERSION_FLAGS.N_VALID_SAMPLES.next = 0;
    assign hwif_in.CONVERSION_FLAGS.PREVIOUS_CONVERSION_CORRUPTED.next = 0;

endmodule
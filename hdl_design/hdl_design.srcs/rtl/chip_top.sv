module chip_top (
    // SPI interfaces
    input  logic adc_csb,
    input  logic adc_scl,
    output logic adc_miso,
    input  logic adc_mosi,
    
    input  logic dac_csb,
    input  logic dac_scl,
    output logic dac_miso,
    input  logic dac_mosi,

    // system clock
    input sysclk,

    // sinegen DAC signals
    output logic sinegen_syncb,
    output logic sinegen_sclk,
    output logic sinegen_dinp,
    output logic sinegen_dinn,

    // SAR ADC signals
    output logic shift_reg_dout,
    output logic shift_reg_sclk,
    output logic shift_reg_den,
    output logic shift_reg_latch,
    input  logic sar_adc_in,
    output logic sh_en,
    output logic int1_en,
    output logic int2_en
);

    logic adc_if_req;
    logic adc_if_rd_en;
    logic adc_if_addr;
    logic adc_if_wr_data;
    logic adc_if_rd_data;
    logic adc_if_rd_err;
    logic adc_if_wr_err;

    logic dac_if_req;
    logic dac_if_rd_en;
    logic dac_if_addr;
    logic dac_if_wr_data;
    logic dac_if_rd_data;
    logic dac_if_rd_err;
    logic dac_if_wr_err;

    spi i_adc_spi (
        .scl(adc_scl),
        .mosi(adc_mosi),
        .miso(adc_miso),
        .cs_b(adc_csb),

        .if_req    (adc_if_req   ),
        .if_rd_en  (adc_if_rd_en ),
        .if_addr   (adc_if_addr  ),
        .if_wr_data(adc_if_wr_dat),
        .if_rd_data(adc_if_rd_dat),
        .if_rd_err (adc_if_rd_err),
        .if_wr_err (adc_if_wr_err)
    );

    spi i_dac_spi (
        .scl (dac_scl),
        .mosi(dac_mosi),
        .miso(dac_miso),
        .cs_b(dac_csb),

        .if_req    (dac_if_req   ),
        .if_rd_en  (dac_if_rd_en ),
        .if_addr   (dac_if_addr  ),
        .if_wr_data(dac_if_wr_dat),
        .if_rd_data(dac_if_rd_dat),
        .if_rd_err (dac_if_rd_err),
        .if_wr_err (dac_if_wr_err)
    );

endmodule
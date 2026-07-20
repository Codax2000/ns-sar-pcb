// Module: chip_top
// Toplevel container module chiefly responsible for managing IO buffer connections.
// Only <adc_top> and <dac_top> are included.
module chip_top (
    // SPI interfaces
    input  logic adc_csb,    
    input  logic dac_csb,
    input  logic scl,
    output logic miso,
    input  logic mosi,

    // system clock
    input sysclk,
    input arst_n,

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

    logic sysclk_buf;
    logic arst_n_buf;
    logic adc_csb_buf;
    logic dac_csb_buf;
    logic scl_buf;
    logic mosi_buf;
    logic miso_buf;

    logic dac_miso;
    logic adc_miso;
    logic dac_miso_en;
    logic adc_miso_en;

    logic sinegen_syncb_buf;
    logic sinegen_sclk_buf;
    logic sinegen_dinp_buf;
    logic sinegen_dinn_buf;

    `ifdef VIVADO
    assign sysclk_buf = sysclk;
    assign arst_n_buf = arst_n;
    assign adc_csb_buf = adc_csb;
    assign dac_csb_buf = dac_csb;
    assign scl_buf = scl;
    assign mosi_buf = mosi;
    assign miso_buf = adc_miso_en ? adc_miso : dac_miso_en ? dac_miso : 1'bz;
    
    assign sinegen_syncb = sinegen_syncb_buf;
    assign sinegen_sclk  = sinegen_sclk_buf;
    assign sinegen_dinp  = sinegen_dinp_buf;
    assign sinegen_dinn  = sinegen_dinn_buf;
    `else
    assign sysclk_buf = sysclk;
    assign arst_n_buf = arst_n;
    assign adc_csb_buf = adc_csb;
    assign dac_csb_buf = dac_csb;
    assign scl_buf = scl;
    assign mosi_buf = mosi;
    assign miso_buf = adc_miso_en ? adc_miso : dac_miso_en ? dac_miso : 1'bz;
    assign miso = miso_buf;

    assign sinegen_syncb = sinegen_syncb_buf;
    assign sinegen_sclk  = sinegen_sclk_buf;
    assign sinegen_dinp  = sinegen_dinp_buf;
    assign sinegen_dinn  = sinegen_dinn_buf;
    `endif

    test_dac_top i_test_dac_top (
        // system clock and reset
        .sysclk(sysclk_buf),
        .arst_n(arst_n_buf),
        
        // SPI interfaces    
        .csb(dac_csb_buf),
        .scl(scl_buf),
        .mosi(mosi_buf),
        .miso(dac_miso),
        .miso_en(dac_miso_en),

        // sinegen DAC signals
        .sinegen_syncb(sinegen_syncb_buf),
        .sinegen_sclk (sinegen_sclk_buf),
        .sinegen_dinp (sinegen_dinp_buf),
        .sinegen_dinn (sinegen_dinn_buf)
    );

    adc_top i_adc_top (
        // system clock and reset
        .sysclk(sysclk_buf),
        .arst_n(arst_n_buf),
        
        // SPI interface    
        .csb(adc_csb_buf),
        .scl(scl_buf),
        .mosi(mosi_buf),
        .miso(adc_miso),
        .miso_en(adc_miso_en)
    );

endmodule
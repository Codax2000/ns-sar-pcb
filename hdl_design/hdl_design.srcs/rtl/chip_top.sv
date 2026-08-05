// Module: chip_top
// Toplevel container module chiefly responsible for managing IO buffer connections.
// Only <adc_top> and <dac_top> are included.
module chip_top (
    // system clock
    input  wire sysclk,
    input  wire arst_n,

    // SPI interfaces
    input  wire adc_csb,    
    input  wire dac_csb,
    input  wire scl,
    output wire miso,
    input  wire mosi,

    // sinegen DAC signals
    output wire sinegen_syncb,
    output wire sinegen_sclk,
    output wire sinegen_dinp,
    output wire sinegen_dinn,

    // SAR ADC signals
    output wire shift_reg_dout,
    output wire shift_reg_sclk,
    output wire shift_reg_den,
    output wire shift_reg_latch,
    input  wire sar_adc_in,
    output wire sh_en,
    output wire int1_en,
    output wire int2_en
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
    // system clock
    logic sysclk_in;
    IBUF i_buf_clk  (.I(sysclk), .O(sysclk_in));
    BUFG i_bufg_clk (.I(sysclk_in), .O(sysclk_buf));

    IBUF i_arst_n_buf (.I(arst_n), .O(arst_n_buf));
    IBUF i_adc_csb_buf (.I(adc_csb), .O(adc_csb_buf));
    IBUF i_dac_csb_buf (.I(dac_csb), .O(dac_csb_buf));
    IBUF i_scl_buf (.I(scl), .O(scl_buf));
    IBUF i_mosi_buf (.I(mosi), .O(mosi_buf));

    assign miso_buf = adc_miso_en ? adc_miso : dac_miso;
    IOBUF i_miso_buf (
        .T(!(adc_miso_en || dac_miso_en)),
        .I(miso_buf),
        .IO(miso)
    );
    
    OBUF i_sinegen_syncb_buf (.I(sinegen_syncb_buf), .O(sinegen_syncb));
    OBUF i_sinegen_sclk_buf  (.I(sinegen_sclk_buf ), .O(sinegen_sclk ));
    OBUF i_sinegen_dinp_buf  (.I(sinegen_dinp_buf ), .O(sinegen_dinp ));
    OBUF i_sinegen_dinn_buf  (.I(sinegen_dinn_buf ), .O(sinegen_dinn ));
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
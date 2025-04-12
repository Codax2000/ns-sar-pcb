module board_top (
    input real i_vip,
    input real i_vin,

    input i_clk,
    input i_arst_b,

    // SPI signals
    input i_scl,
    input i_mosi,
    input i_csb,
    output o_miso
);

    localparam real VDD=3.3,
    localparam N_QUANTIZER_BITS=3

    analog_core #(
        .VDD(VDD),
        .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    ) ana_core_model (
        // TODO: add ports
    );

    top_level dig_core (
        // TODO: add ports
    );

endmodule
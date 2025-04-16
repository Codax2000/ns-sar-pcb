module board_top (
    if_input.hardware_port vin,

    input i_clk,
    input i_arst_b,

    // SPI signals
    spi_input spi
);

    localparam real VDD=3.3,
    localparam N_QUANTIZER_BITS=3

    analog_core #(
        .VDD(VDD),
        .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    ) analog_core_model (
        // TODO: add ports
    );

    digcore dig_core (
        // TODO: add ports
    );

endmodule
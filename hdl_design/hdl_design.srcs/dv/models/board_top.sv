module board_top (
    if_input.hardware_port vin,

    if_clkgen clkgen,

    if_spi spi
);

    localparam real VDD=3.3,
    localparam N_QUANTIZER_BITS=3

    analog_frontend #(
        .VDD(VDD),
        .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    ) analog_core_model (
        // TODO: add ports
    );

    digcore dig_core (
        // TODO: add ports
    );

endmodule
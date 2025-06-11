module board_top (
    if_input.hardware_port vin,

    if_clkgen.module_clkgen clkgen,

    if_spi spi
);

    parameter real VDD=3.3;
    parameter N_QUANTIZER_BITS=3;

    if_analog_to_fpga #(
        .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    ) if_digital ();

    // analog_core #(
    //     .VDD(VDD),
    //     .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    // ) analog_core_model (
    //     .signal_in(vin),
    //     .if_digital
    // );

    dig_core #(
        .N_SAR_BITS(N_QUANTIZER_BITS)
    ) DIGTOP (
        .i_sar_compare(if_digital.compare),
        .i_sysclk(clkgen.clk),
        .i_sysrst_b(clkgen.rst_b),
        //TODO: deal with analog/digital boundary later
        .i_cs_b(spi.csb),
        .i_scl(spi.scl),
        .i_mosi(spi.mosi),
        .o_miso(spi.miso)
    );

endmodule
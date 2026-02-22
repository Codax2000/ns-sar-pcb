module board_top #(
    parameter N_QUANTIZER_BITS = 3
) (
    input real vdd,

    input logic clk,
    input logic arst_n,

    input real vinp,
    input real vinn,

    spi_if spi_signals
);

    // if_analog_to_fpga #(
    //     .N_QUANTIZER_BITS(N_QUANTIZER_BITS)
    // ) if_digital ();

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
        //TODO: deal with analog/digital boundary later
        .i_sar_compare(0),

        .i_sysclk(clk),
        .i_sysrst_b(arst_n),

        .i_cs_b(spi.csb),
        .i_scl(spi.scl),
        .i_mosi(spi.mosi),
        .o_miso(spi.miso)
    );

endmodule
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

    spi #(
        .ADDR_BYTES(2)
    ) i_spi (
        .scl(i_scl),
        .mosi(i_mosi),
        .miso(o_miso),
        .cs_b(i_cs_b)
    );

endmodule
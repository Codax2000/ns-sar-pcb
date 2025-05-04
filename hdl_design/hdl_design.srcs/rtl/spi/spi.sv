module spi #(
    parameter DATA_WIDTH=16,
    parameter ADDR_WIDTH=4
) (
    if_spi if,
    if_reg reg,
    input logic i_clk,

    // FIFO interface
    logic o_start_coversion,
    logic i_fifo_full,

    // Mem read interface
    output logic 
);

endmodule
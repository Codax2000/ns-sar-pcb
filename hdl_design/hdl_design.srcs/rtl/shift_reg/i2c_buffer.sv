/**
Module: i2c_buffer

This module takes in data to send over I2C and transmits it. The input data is
write-only, that is, this module only supports writing to external modules,
not reading from them. It has a simple valid/ready handshake for input data.
*/
module i2c_buffer # (
    parameter N_ADDRESS_BYTES = 2,
    parameter N_WRITE_BYTES = 2,
) (
    input logic [N_WRITE_BYTES-1:0][7:0] addr,
    input logic [N_WRITE_BYTES-1:0][7:0] data,
    input logic [$clog2(N_WRITE_BYTES)-1:0] n_data_bytes,
    input logic                          valid,
    output logic                         ready,

    input logic 
    input logic clk,
    input logic rst_n
);

    enum logic [1:0] {
        READY,
        SEND_ADDRESS,
        SEND_DATA
    } state, next_state;

    logic [2:0] counter;

endmodule
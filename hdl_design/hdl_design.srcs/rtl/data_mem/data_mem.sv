/**
Alex Knowlton
5/3/2025

Defines a memory with a single R/W port on clock A and a second read port on
clock B, with synchronous read on the next cycle. No reset, but reads out X
if has not been written.

Port A has write-before-read capability, so keeping address the same will
read out the value written on the previous clock cycle, if any
*/

module data_mem #(
    parameter ADDR_WIDTH=20,  // defines maximum NFFT
    parameter DATA_WIDTH=16
) (
    input logic clka,
    input logic [ADDR_WIDTH-1:0] addr_a,
    input logic [DATA_WIDTH-1:0] wr_data_a,
    output logic [DATA_WIDTH-1:0] rd_data_a,
    input logic wr_enable_a,

    input logic clkb,
    input logic [ADDR_WIDTH-1:0] addr_b,
    output logic [DATA_WIDTH-1:0] rd_data_b
);
    localparam MEM_DEPTH = 1 << ADDR_WIDTH;
    logic [DATA_WIDTH-1:0] mem [MEM_DEPTH-1:0];

    always_ff @(posedge clka) begin
        if (wr_enable_a) begin
            mem[addr_a] <= wr_data_a;
            rd_data_a <= wr_data_a; // write-before-read
        end else begin
            rd_data_a <= mem[addr_a];
        end
    end

    always_ff @(posedge clkb)
        rd_data_b <= mem[addr_b];

endmodule
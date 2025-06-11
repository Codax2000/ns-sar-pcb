module simple_data_mem(
    input logic i_clk,
    input logic [3:0] rd_addr,
    output logic [15:0] out_data
);

    logic [15:0] arr [1:0];

    initial begin
        arr[0] = 16'hDEAF;
        arr[1] = 16'hCAFE;
    end

    always_ff @(posedge i_clk)
        out_data <= arr[rd_addr[0]];
endmodule
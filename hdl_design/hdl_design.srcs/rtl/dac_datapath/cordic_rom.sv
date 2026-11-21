module atan_rom (
    input  logic        clk,
    input  logic        rst,
    input  logic        rd_en,
    input  logic [3:0]  addr,
    output logic [15:0] data
);

    logic [15:0] data_out;

    always_comb begin
        case (addr)
            4'd0:  data_out = 16'd8192;
            4'd1:  data_out = 16'd4836;
            4'd2:  data_out = 16'd2555;
            4'd3:  data_out = 16'd1297;
            4'd4:  data_out = 16'd651;
            4'd5:  data_out = 16'd326;
            4'd6:  data_out = 16'd163;
            4'd7:  data_out = 16'd81;
            4'd8:  data_out = 16'd41;
            4'd9:  data_out = 16'd20;
            4'd10: data_out = 16'd10;
            4'd11: data_out = 16'd5;
            4'd12: data_out = 16'd3;
            4'd13: data_out = 16'd1;
            4'd14: data_out = 16'd1;
            4'd15: data_out = 16'd0;
            default: data_out = 16'd0;
        endcase
    end

    always_ff @(posedge clk) begin : data_out_reg
        if (rst) begin
            data <= 16'd0;
        end
        else if (rd_en) begin
            data <= data_out;
        end
    end : data_out_reg
    
endmodule
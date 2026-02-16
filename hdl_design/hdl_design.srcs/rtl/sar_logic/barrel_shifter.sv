module barrel_shifter #(
    parameter N_SAR_BITS=3
) (
    input  logic [(1<<N_SAR_BITS)-1:0] i_data,
    input  logic [N_SAR_BITS-1:0]      i_shift,
    output logic [(1<<N_SAR_BITS)-1:0] o_data
);

    logic [(1<<(N_SAR_BITS+1))-1:0] input_shift_data;
    
    assign input_shift_data = {i_data, {(1<<N_SAR_BITS){1'b0}}} >> i_shift;

    assign o_data = input_shift_data[(1<<(N_SAR_BITS+1))-1:(1<<(N_SAR_BITS))] |
                    input_shift_data[(1<<(N_SAR_BITS))-1:0];

endmodule
module binary_to_thermometer #(
    parameter N_BINARY_BITS=3
) (
    input logic [N_BINARY_BITS-1:0] i_binary,
    output logic [(1<<N_BINARY_BITS)-1:0] o_thermometer;
);

    genvar i;

    always_comb begin
        for (i = 0; i < (1 << N_BINARY_BITS); i++) begin
            o_thermometer[i] = i < i_binary;
        end
    end

endmodule
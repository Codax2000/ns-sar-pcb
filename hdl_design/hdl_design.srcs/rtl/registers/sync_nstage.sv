module sync_nstage #(
    parameter N_BITS=1,
    parameter N_SYNC_STAGES=2
) (
    input logic [N_BITS-1:0] src_data,
    output logic [N_BITS-1:0] dest_data,
    input logic src_clk,
    input logic dest_clk,
    input logic dest_clk_rst
);

    logic [N_BITS-1:0] sync_to_dest_clk [(N_SYNC_STAGES-1):0];
    logic [N_BITS-1:0] sync_to_src_clk;
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge dest_clk or dest_clk_rst) begin
            if (dest_clk_rst) begin
                sync_to_dest_clk[i] <= 0;
            end
            else begin
                if (i == 0)
                    sync_to_dest_clk[i] <= sync_to_src_clk;
                else
                    sync_to_dest_clk[i] <= sync_to_dest_clk[i - 1];
            end
        end
    end
    assign dest_data = sync_to_dest_clk[N_SYNC_STAGES - 1];

    always_comb
        sync_to_src_clk = src_data;

endmodule
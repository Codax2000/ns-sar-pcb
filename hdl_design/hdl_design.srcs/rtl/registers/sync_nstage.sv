module #(
    parameter N_BITS=1,
    parameter N_SYNC_STAGES=2,
    parameter SRC_INPUT_REG=0
) sync_nstage (
    logic [N_BITS-1:0] src_data,
    logic [N_BITS-1:0] dest_data,
    logic src_clk,
    logic dest_clk
);

    `ifdef VIVADO

    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(N_BITS),
        .SRC_INPUT_REG(SRC_INPUT_REG)
    ) cdc_sync (
        .src_in  (src_data),
        .dest_out(dest_data),
        .dest_clk(dest_clk),
        .src_clk(src_clk)
    );

    `else

    logic [N_BITS-1:0] sync_to_dest_clk [(N_SYNC_STAGES-1):0];
    logic [N_BITS-1:0] sync_to_src_clk;
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge dest_clk) begin
            if (i == 0)
                sync_to_dest_clk[i] <= sync_to_src_clk;
            else
                sync_to_dest_clk[i] <= sync_to_dest_clk[i - 1];
        end
    end
    assign dest_data = sync_to_dest_clk[N_SYNC_STAGES - 1];

    if (SRC_INPUT_REG) begin
        always_ff @(posedge src_clk)
            sync_to_src_clk <= src_data;
    end else begin
        always_comb
            sync_to_src_clk = src_data;
    end
    
    `endif

endmodule
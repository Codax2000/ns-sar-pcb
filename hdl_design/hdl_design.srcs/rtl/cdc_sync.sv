module cdc_sync #(
    parameter N_SYNC_STAGES=2
) (
    input  logic i_dwa,
    output logic o_dwa,
    input  logic [2:0] i_osr_power,
    output logic [2:0] o_osr_power,
    input  logic [3:0] i_nfft_power,
    output logic [3:0] o_nfft_power,
    input  logic [3:0] i_clk_div,
    output logic [3:0] o_clk_div,

    input  logic [1:0] i_fsm_status,
    output logic [1:0] o_fsm_status,

    input  logic i_clk_spi,
    input  logic i_clk_sys
);

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(12),
        .SRC_INPUT_REG(0) // already registered, so not necessary
    ) cdc_sync_to_sysclk (
        .src_in  ({i_nfft_power, i_dwa, i_osr_power, i_clk_div}),
        .dest_out({o_nfft_power, o_dwa, o_osr_power, o_clk_div}),
        .dest_clk(i_clk_sys),
        .src_clk (i_clk_spi)
    );
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(2),
        .SRC_INPUT_REG(0) // also already registered
    ) cdc_sync_to_spiclk (
        .src_in(i_fsm_status),
        .dest_out(o_fsm_status),
        .dest_clk(i_clk_spi),
        .src_clk(i_clk_sys)
    );
    `else
    logic [11:0] sync_mid_to_sysclk [(N_SYNC_STAGES-1):0];
    genvar i;
    generate
        for (i = 0; i < N_SYNC_STAGES; i++) begin
            always_ff @(posedge i_clk_sys) begin
                if (i == 0)
                    sync_mid_to_sysclk[i] <= {i_nfft_power, i_dwa, i_osr_power, i_clk_div};
                else
                    sync_mid_to_sysclk[i] <= sync_mid_to_sysclk[i - 1];
            end
        end
    endgenerate
    assign {o_nfft_power, o_dwa, o_osr_power, o_clk_div} = sync_mid_to_sysclk[N_SYNC_STAGES-1];
    
    logic [1:0] sync_mid_to_spiclk [(N_SYNC_STAGES-1):0];
    genvar i;
    generate
        for (i = 0; i < N_SYNC_STAGES; i++) begin
            always_ff @(posedge i_clk_sys) begin
                if (i == 0)
                    sync_mid_to_spiclk[i] <= i_fsm_status;
                else
                    sync_mid_to_spiclk[i] <= sync_mid_to_spiclk[i - 1];
            end
        end
    endgenerate
    assign o_fsm_status = sync_mid_to_spiclk[N_SYNC_STAGES-1];
    `endif

endmodule
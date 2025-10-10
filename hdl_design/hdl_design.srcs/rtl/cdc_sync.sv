module cdc_sync #(
    parameter N_SYNC_STAGES=3
) (
    reg_if.WR_BUS_CLK bus_clk_reg,
    reg_if.WR_SYS_CLK sys_clk_reg,
    input logic sys_clk,
    input logic bus_clk
);

    // RO registers, sys_clk -> bus_clk
    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(3),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_bus_clk_MAIN_STATE_RB (
        .src_in  (sys_clk_reg.MAIN_STATE_RB),
        .dest_out(bus_clk_reg.MAIN_STATE_RB),
        .dest_clk(bus_clk),
        .src_clk(sys_clk)
    );
    `else
    logic [2:0] sync_to_bus_clk_MAIN_STATE_RB [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge bus_clk) begin
            if (i == 0)
                sync_to_bus_clk_MAIN_STATE_RB[i] <= sys_clk_reg.MAIN_STATE_RB;
            else
                sync_to_bus_clk_MAIN_STATE_RB[i] <= sync_to_bus_clk_MAIN_STATE_RB[i - 1];
        end
    end
    assign bus_clk_reg.MAIN_STATE_RB = sync_to_bus_clk_MAIN_STATE_RB[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_bus_clk_CLKGEN_DRP_DO (
        .src_in  (sys_clk_reg.CLKGEN_DRP_DO),
        .dest_out(bus_clk_reg.CLKGEN_DRP_DO),
        .dest_clk(bus_clk),
        .src_clk(sys_clk)
    );
    `else
    logic [15:0] sync_to_bus_clk_CLKGEN_DRP_DO [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge bus_clk) begin
            if (i == 0)
                sync_to_bus_clk_CLKGEN_DRP_DO[i] <= sys_clk_reg.CLKGEN_DRP_DO;
            else
                sync_to_bus_clk_CLKGEN_DRP_DO[i] <= sync_to_bus_clk_CLKGEN_DRP_DO[i - 1];
        end
    end
    assign bus_clk_reg.CLKGEN_DRP_DO = sync_to_bus_clk_CLKGEN_DRP_DO[N_SYNC_STAGES - 1];
    `endif

    // RO registers, bus_clk -> sys_clk
    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(14),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_NFFT_POWER (
        .src_in  (bus_clk_reg.NFFT_POWER),
        .dest_out(sys_clk_reg.NFFT_POWER),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [13:0] sync_to_sys_clk_NFFT_POWER [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_NFFT_POWER[i] <= bus_clk_reg.NFFT_POWER;
            else
                sync_to_sys_clk_NFFT_POWER[i] <= sync_to_sys_clk_NFFT_POWER[i - 1];
        end
    end
    assign sys_clk_reg.NFFT_POWER = sync_to_sys_clk_NFFT_POWER[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(1),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_DWA_EN (
        .src_in  (bus_clk_reg.DWA_EN),
        .dest_out(sys_clk_reg.DWA_EN),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [0:0] sync_to_sys_clk_DWA_EN [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_DWA_EN[i] <= bus_clk_reg.DWA_EN;
            else
                sync_to_sys_clk_DWA_EN[i] <= sync_to_sys_clk_DWA_EN[i - 1];
        end
    end
    assign sys_clk_reg.DWA_EN = sync_to_sys_clk_DWA_EN[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(8),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_OSR_POWER (
        .src_in  (bus_clk_reg.OSR_POWER),
        .dest_out(sys_clk_reg.OSR_POWER),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [7:0] sync_to_sys_clk_OSR_POWER [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_OSR_POWER[i] <= bus_clk_reg.OSR_POWER;
            else
                sync_to_sys_clk_OSR_POWER[i] <= sync_to_sys_clk_OSR_POWER[i - 1];
        end
    end
    assign sys_clk_reg.OSR_POWER = sync_to_sys_clk_OSR_POWER[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_SH_TOTAL_CYCLES (
        .src_in  (bus_clk_reg.N_SH_TOTAL_CYCLES),
        .dest_out(sys_clk_reg.N_SH_TOTAL_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_SH_TOTAL_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_SH_TOTAL_CYCLES[i] <= bus_clk_reg.N_SH_TOTAL_CYCLES;
            else
                sync_to_sys_clk_N_SH_TOTAL_CYCLES[i] <= sync_to_sys_clk_N_SH_TOTAL_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_SH_TOTAL_CYCLES = sync_to_sys_clk_N_SH_TOTAL_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_SH_ACTIVE_CYCLES (
        .src_in  (bus_clk_reg.N_SH_ACTIVE_CYCLES),
        .dest_out(sys_clk_reg.N_SH_ACTIVE_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_SH_ACTIVE_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_SH_ACTIVE_CYCLES[i] <= bus_clk_reg.N_SH_ACTIVE_CYCLES;
            else
                sync_to_sys_clk_N_SH_ACTIVE_CYCLES[i] <= sync_to_sys_clk_N_SH_ACTIVE_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_SH_ACTIVE_CYCLES = sync_to_sys_clk_N_SH_ACTIVE_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES (
        .src_in  (bus_clk_reg.N_BOTTOM_PLATE_ACTIVE_CYCLES),
        .dest_out(sys_clk_reg.N_BOTTOM_PLATE_ACTIVE_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES[i] <= bus_clk_reg.N_BOTTOM_PLATE_ACTIVE_CYCLES;
            else
                sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES[i] <= sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_BOTTOM_PLATE_ACTIVE_CYCLES = sync_to_sys_clk_N_BOTTOM_PLATE_ACTIVE_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_SAR_CYCLES (
        .src_in  (bus_clk_reg.N_SAR_CYCLES),
        .dest_out(sys_clk_reg.N_SAR_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_SAR_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_SAR_CYCLES[i] <= bus_clk_reg.N_SAR_CYCLES;
            else
                sync_to_sys_clk_N_SAR_CYCLES[i] <= sync_to_sys_clk_N_SAR_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_SAR_CYCLES = sync_to_sys_clk_N_SAR_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_INT1_TOTAL_CYCLES (
        .src_in  (bus_clk_reg.N_INT1_TOTAL_CYCLES),
        .dest_out(sys_clk_reg.N_INT1_TOTAL_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_INT1_TOTAL_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_INT1_TOTAL_CYCLES[i] <= bus_clk_reg.N_INT1_TOTAL_CYCLES;
            else
                sync_to_sys_clk_N_INT1_TOTAL_CYCLES[i] <= sync_to_sys_clk_N_INT1_TOTAL_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_INT1_TOTAL_CYCLES = sync_to_sys_clk_N_INT1_TOTAL_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_INT1_ACTIVE_CYCLES (
        .src_in  (bus_clk_reg.N_INT1_ACTIVE_CYCLES),
        .dest_out(sys_clk_reg.N_INT1_ACTIVE_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_INT1_ACTIVE_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_INT1_ACTIVE_CYCLES[i] <= bus_clk_reg.N_INT1_ACTIVE_CYCLES;
            else
                sync_to_sys_clk_N_INT1_ACTIVE_CYCLES[i] <= sync_to_sys_clk_N_INT1_ACTIVE_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_INT1_ACTIVE_CYCLES = sync_to_sys_clk_N_INT1_ACTIVE_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_INT2_TOTAL_CYCLES (
        .src_in  (bus_clk_reg.N_INT2_TOTAL_CYCLES),
        .dest_out(sys_clk_reg.N_INT2_TOTAL_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_INT2_TOTAL_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_INT2_TOTAL_CYCLES[i] <= bus_clk_reg.N_INT2_TOTAL_CYCLES;
            else
                sync_to_sys_clk_N_INT2_TOTAL_CYCLES[i] <= sync_to_sys_clk_N_INT2_TOTAL_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_INT2_TOTAL_CYCLES = sync_to_sys_clk_N_INT2_TOTAL_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_N_INT2_ACTIVE_CYCLES (
        .src_in  (bus_clk_reg.N_INT2_ACTIVE_CYCLES),
        .dest_out(sys_clk_reg.N_INT2_ACTIVE_CYCLES),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_N_INT2_ACTIVE_CYCLES [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_N_INT2_ACTIVE_CYCLES[i] <= bus_clk_reg.N_INT2_ACTIVE_CYCLES;
            else
                sync_to_sys_clk_N_INT2_ACTIVE_CYCLES[i] <= sync_to_sys_clk_N_INT2_ACTIVE_CYCLES[i - 1];
        end
    end
    assign sys_clk_reg.N_INT2_ACTIVE_CYCLES = sync_to_sys_clk_N_INT2_ACTIVE_CYCLES[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(1),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_START_CONVERSION (
        .src_in  (bus_clk_reg.START_CONVERSION),
        .dest_out(sys_clk_reg.START_CONVERSION),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [0:0] sync_to_sys_clk_START_CONVERSION [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_START_CONVERSION[i] <= bus_clk_reg.START_CONVERSION;
            else
                sync_to_sys_clk_START_CONVERSION[i] <= sync_to_sys_clk_START_CONVERSION[i - 1];
        end
    end
    assign sys_clk_reg.START_CONVERSION = sync_to_sys_clk_START_CONVERSION[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(7),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_CLKGEN_DRP_DADDR (
        .src_in  (bus_clk_reg.CLKGEN_DRP_DADDR),
        .dest_out(sys_clk_reg.CLKGEN_DRP_DADDR),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [6:0] sync_to_sys_clk_CLKGEN_DRP_DADDR [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_CLKGEN_DRP_DADDR[i] <= bus_clk_reg.CLKGEN_DRP_DADDR;
            else
                sync_to_sys_clk_CLKGEN_DRP_DADDR[i] <= sync_to_sys_clk_CLKGEN_DRP_DADDR[i - 1];
        end
    end
    assign sys_clk_reg.CLKGEN_DRP_DADDR = sync_to_sys_clk_CLKGEN_DRP_DADDR[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(16),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_CLKGEN_DRP_DI (
        .src_in  (bus_clk_reg.CLKGEN_DRP_DI),
        .dest_out(sys_clk_reg.CLKGEN_DRP_DI),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [15:0] sync_to_sys_clk_CLKGEN_DRP_DI [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_CLKGEN_DRP_DI[i] <= bus_clk_reg.CLKGEN_DRP_DI;
            else
                sync_to_sys_clk_CLKGEN_DRP_DI[i] <= sync_to_sys_clk_CLKGEN_DRP_DI[i - 1];
        end
    end
    assign sys_clk_reg.CLKGEN_DRP_DI = sync_to_sys_clk_CLKGEN_DRP_DI[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(1),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_CLKGEN_DRP_RD_EN (
        .src_in  (bus_clk_reg.CLKGEN_DRP_RD_EN),
        .dest_out(sys_clk_reg.CLKGEN_DRP_RD_EN),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [0:0] sync_to_sys_clk_CLKGEN_DRP_RD_EN [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_CLKGEN_DRP_RD_EN[i] <= bus_clk_reg.CLKGEN_DRP_RD_EN;
            else
                sync_to_sys_clk_CLKGEN_DRP_RD_EN[i] <= sync_to_sys_clk_CLKGEN_DRP_RD_EN[i - 1];
        end
    end
    assign sys_clk_reg.CLKGEN_DRP_RD_EN = sync_to_sys_clk_CLKGEN_DRP_RD_EN[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(1),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_CLKGEN_DRP_WR_EN (
        .src_in  (bus_clk_reg.CLKGEN_DRP_WR_EN),
        .dest_out(sys_clk_reg.CLKGEN_DRP_WR_EN),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [0:0] sync_to_sys_clk_CLKGEN_DRP_WR_EN [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_CLKGEN_DRP_WR_EN[i] <= bus_clk_reg.CLKGEN_DRP_WR_EN;
            else
                sync_to_sys_clk_CLKGEN_DRP_WR_EN[i] <= sync_to_sys_clk_CLKGEN_DRP_WR_EN[i - 1];
        end
    end
    assign sys_clk_reg.CLKGEN_DRP_WR_EN = sync_to_sys_clk_CLKGEN_DRP_WR_EN[N_SYNC_STAGES - 1];
    `endif

    `ifdef VIVADO
    xpm_cdc_array_single #(
        .DEST_SYNC_FF(N_SYNC_STAGES),
        .WIDTH(1),
        .SRC_INPUT_REG(0)
    ) cdc_sync_to_sys_clk_CLKGEN_DRP_DEN (
        .src_in  (bus_clk_reg.CLKGEN_DRP_DEN),
        .dest_out(sys_clk_reg.CLKGEN_DRP_DEN),
        .dest_clk(sys_clk),
        .src_clk(bus_clk)
    );
    `else
    logic [0:0] sync_to_sys_clk_CLKGEN_DRP_DEN [(N_SYNC_STAGES-1):0];
    genvar i;
    for (i = 0; i < N_SYNC_STAGES; i++) begin
        always_ff @(posedge sys_clk) begin
            if (i == 0)
                sync_to_sys_clk_CLKGEN_DRP_DEN[i] <= bus_clk_reg.CLKGEN_DRP_DEN;
            else
                sync_to_sys_clk_CLKGEN_DRP_DEN[i] <= sync_to_sys_clk_CLKGEN_DRP_DEN[i - 1];
        end
    end
    assign sys_clk_reg.CLKGEN_DRP_DEN = sync_to_sys_clk_CLKGEN_DRP_DEN[N_SYNC_STAGES - 1];
    `endif

endmodule

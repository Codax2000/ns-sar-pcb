module registers(
    reg_if              i0,
    input  logic        clk,
    input  logic        rst_b,
    input  logic [13:0] bus_if_wr_addr,
    input  logic [15:0] bus_if_wr_data,
    input  logic        bus_if_wr_en,
    input  logic [13:0] bus_if_rd_addr,
    output logic [15:0] bus_if_rd_data,
    input  logic        bus_if_rd_en
);

    // generated RW register write logic
    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.NFFT_POWER <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd0))
            i0.NFFT_POWER <= bus_if_wr_data[13:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.DWA_EN <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd0))
            i0.DWA_EN <= bus_if_wr_data[15];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.OSR_POWER <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd1))
            i0.OSR_POWER <= bus_if_wr_data[7:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_SH_TOTAL_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd2))
            i0.N_SH_TOTAL_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_SH_ACTIVE_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd3))
            i0.N_SH_ACTIVE_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_BOTTOM_PLATE_ACTIVE_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd4))
            i0.N_BOTTOM_PLATE_ACTIVE_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_SAR_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd5))
            i0.N_SAR_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_INT1_TOTAL_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd6))
            i0.N_INT1_TOTAL_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_INT1_ACTIVE_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd7))
            i0.N_INT1_ACTIVE_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_INT2_TOTAL_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd8))
            i0.N_INT2_TOTAL_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.N_INT2_ACTIVE_CYCLES <= 'd1;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd9))
            i0.N_INT2_ACTIVE_CYCLES <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.CLKGEN_DRP_DADDR <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd11))
            i0.CLKGEN_DRP_DADDR <= bus_if_wr_data[6:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.CLKGEN_DRP_DI <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd12))
            i0.CLKGEN_DRP_DI <= bus_if_wr_data[15:0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.CLKGEN_DRP_RD_EN <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd14))
            i0.CLKGEN_DRP_RD_EN <= bus_if_wr_data[0];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.CLKGEN_DRP_WR_EN <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd14))
            i0.CLKGEN_DRP_WR_EN <= bus_if_wr_data[1];
    end

    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.CLKGEN_DRP_DEN <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd14))
            i0.CLKGEN_DRP_DEN <= bus_if_wr_data[2];
    end


    // generated W1C register set/clear logic
    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            i0.START_CONVERSION <= 'd0;
        else if (bus_if_wr_en && (bus_if_wr_addr == 'd10))
            i0.START_CONVERSION <= (i0.START_CONVERSION & (~bus_if_wr_data[0])) | (i0.START_CONVERSION_set);
        else
            i0.START_CONVERSION <= (i0.START_CONVERSION) | (i0.START_CONVERSION_set);
    end

    // synchronous readback data
    always_ff @(posedge clk or negedge rst_b) begin
        if (!rst_b)
            bus_if_rd_data <= '0;
        else if (bus_if_rd_en) begin
            case (bus_if_rd_addr)
                0 : bus_if_rd_data <= '{i0.DWA_EN, 1'b0, i0.NFFT_POWER[13], i0.NFFT_POWER[12], i0.NFFT_POWER[11], i0.NFFT_POWER[10], i0.NFFT_POWER[9], i0.NFFT_POWER[8], i0.NFFT_POWER[7], i0.NFFT_POWER[6], i0.NFFT_POWER[5], i0.NFFT_POWER[4], i0.NFFT_POWER[3], i0.NFFT_POWER[2], i0.NFFT_POWER[1], i0.NFFT_POWER[0]};
                1 : bus_if_rd_data <= '{1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i0.OSR_POWER[7], i0.OSR_POWER[6], i0.OSR_POWER[5], i0.OSR_POWER[4], i0.OSR_POWER[3], i0.OSR_POWER[2], i0.OSR_POWER[1], i0.OSR_POWER[0]};
                2 : bus_if_rd_data <= '{i0.N_SH_TOTAL_CYCLES[15], i0.N_SH_TOTAL_CYCLES[14], i0.N_SH_TOTAL_CYCLES[13], i0.N_SH_TOTAL_CYCLES[12], i0.N_SH_TOTAL_CYCLES[11], i0.N_SH_TOTAL_CYCLES[10], i0.N_SH_TOTAL_CYCLES[9], i0.N_SH_TOTAL_CYCLES[8], i0.N_SH_TOTAL_CYCLES[7], i0.N_SH_TOTAL_CYCLES[6], i0.N_SH_TOTAL_CYCLES[5], i0.N_SH_TOTAL_CYCLES[4], i0.N_SH_TOTAL_CYCLES[3], i0.N_SH_TOTAL_CYCLES[2], i0.N_SH_TOTAL_CYCLES[1], i0.N_SH_TOTAL_CYCLES[0]};
                3 : bus_if_rd_data <= '{i0.N_SH_ACTIVE_CYCLES[15], i0.N_SH_ACTIVE_CYCLES[14], i0.N_SH_ACTIVE_CYCLES[13], i0.N_SH_ACTIVE_CYCLES[12], i0.N_SH_ACTIVE_CYCLES[11], i0.N_SH_ACTIVE_CYCLES[10], i0.N_SH_ACTIVE_CYCLES[9], i0.N_SH_ACTIVE_CYCLES[8], i0.N_SH_ACTIVE_CYCLES[7], i0.N_SH_ACTIVE_CYCLES[6], i0.N_SH_ACTIVE_CYCLES[5], i0.N_SH_ACTIVE_CYCLES[4], i0.N_SH_ACTIVE_CYCLES[3], i0.N_SH_ACTIVE_CYCLES[2], i0.N_SH_ACTIVE_CYCLES[1], i0.N_SH_ACTIVE_CYCLES[0]};
                4 : bus_if_rd_data <= '{i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[15], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[14], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[13], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[12], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[11], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[10], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[9], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[8], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[7], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[6], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[5], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[4], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[3], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[2], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[1], i0.N_BOTTOM_PLATE_ACTIVE_CYCLES[0]};
                5 : bus_if_rd_data <= '{i0.N_SAR_CYCLES[15], i0.N_SAR_CYCLES[14], i0.N_SAR_CYCLES[13], i0.N_SAR_CYCLES[12], i0.N_SAR_CYCLES[11], i0.N_SAR_CYCLES[10], i0.N_SAR_CYCLES[9], i0.N_SAR_CYCLES[8], i0.N_SAR_CYCLES[7], i0.N_SAR_CYCLES[6], i0.N_SAR_CYCLES[5], i0.N_SAR_CYCLES[4], i0.N_SAR_CYCLES[3], i0.N_SAR_CYCLES[2], i0.N_SAR_CYCLES[1], i0.N_SAR_CYCLES[0]};
                6 : bus_if_rd_data <= '{i0.N_INT1_TOTAL_CYCLES[15], i0.N_INT1_TOTAL_CYCLES[14], i0.N_INT1_TOTAL_CYCLES[13], i0.N_INT1_TOTAL_CYCLES[12], i0.N_INT1_TOTAL_CYCLES[11], i0.N_INT1_TOTAL_CYCLES[10], i0.N_INT1_TOTAL_CYCLES[9], i0.N_INT1_TOTAL_CYCLES[8], i0.N_INT1_TOTAL_CYCLES[7], i0.N_INT1_TOTAL_CYCLES[6], i0.N_INT1_TOTAL_CYCLES[5], i0.N_INT1_TOTAL_CYCLES[4], i0.N_INT1_TOTAL_CYCLES[3], i0.N_INT1_TOTAL_CYCLES[2], i0.N_INT1_TOTAL_CYCLES[1], i0.N_INT1_TOTAL_CYCLES[0]};
                7 : bus_if_rd_data <= '{i0.N_INT1_ACTIVE_CYCLES[15], i0.N_INT1_ACTIVE_CYCLES[14], i0.N_INT1_ACTIVE_CYCLES[13], i0.N_INT1_ACTIVE_CYCLES[12], i0.N_INT1_ACTIVE_CYCLES[11], i0.N_INT1_ACTIVE_CYCLES[10], i0.N_INT1_ACTIVE_CYCLES[9], i0.N_INT1_ACTIVE_CYCLES[8], i0.N_INT1_ACTIVE_CYCLES[7], i0.N_INT1_ACTIVE_CYCLES[6], i0.N_INT1_ACTIVE_CYCLES[5], i0.N_INT1_ACTIVE_CYCLES[4], i0.N_INT1_ACTIVE_CYCLES[3], i0.N_INT1_ACTIVE_CYCLES[2], i0.N_INT1_ACTIVE_CYCLES[1], i0.N_INT1_ACTIVE_CYCLES[0]};
                8 : bus_if_rd_data <= '{i0.N_INT2_TOTAL_CYCLES[15], i0.N_INT2_TOTAL_CYCLES[14], i0.N_INT2_TOTAL_CYCLES[13], i0.N_INT2_TOTAL_CYCLES[12], i0.N_INT2_TOTAL_CYCLES[11], i0.N_INT2_TOTAL_CYCLES[10], i0.N_INT2_TOTAL_CYCLES[9], i0.N_INT2_TOTAL_CYCLES[8], i0.N_INT2_TOTAL_CYCLES[7], i0.N_INT2_TOTAL_CYCLES[6], i0.N_INT2_TOTAL_CYCLES[5], i0.N_INT2_TOTAL_CYCLES[4], i0.N_INT2_TOTAL_CYCLES[3], i0.N_INT2_TOTAL_CYCLES[2], i0.N_INT2_TOTAL_CYCLES[1], i0.N_INT2_TOTAL_CYCLES[0]};
                9 : bus_if_rd_data <= '{i0.N_INT2_ACTIVE_CYCLES[15], i0.N_INT2_ACTIVE_CYCLES[14], i0.N_INT2_ACTIVE_CYCLES[13], i0.N_INT2_ACTIVE_CYCLES[12], i0.N_INT2_ACTIVE_CYCLES[11], i0.N_INT2_ACTIVE_CYCLES[10], i0.N_INT2_ACTIVE_CYCLES[9], i0.N_INT2_ACTIVE_CYCLES[8], i0.N_INT2_ACTIVE_CYCLES[7], i0.N_INT2_ACTIVE_CYCLES[6], i0.N_INT2_ACTIVE_CYCLES[5], i0.N_INT2_ACTIVE_CYCLES[4], i0.N_INT2_ACTIVE_CYCLES[3], i0.N_INT2_ACTIVE_CYCLES[2], i0.N_INT2_ACTIVE_CYCLES[1], i0.N_INT2_ACTIVE_CYCLES[0]};
                10 : bus_if_rd_data <= '{1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i0.MAIN_STATE_RB[2], i0.MAIN_STATE_RB[1], i0.MAIN_STATE_RB[0], i0.START_CONVERSION};
                11 : bus_if_rd_data <= '{1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i0.CLKGEN_DRP_DADDR[6], i0.CLKGEN_DRP_DADDR[5], i0.CLKGEN_DRP_DADDR[4], i0.CLKGEN_DRP_DADDR[3], i0.CLKGEN_DRP_DADDR[2], i0.CLKGEN_DRP_DADDR[1], i0.CLKGEN_DRP_DADDR[0]};
                12 : bus_if_rd_data <= '{i0.CLKGEN_DRP_DI[15], i0.CLKGEN_DRP_DI[14], i0.CLKGEN_DRP_DI[13], i0.CLKGEN_DRP_DI[12], i0.CLKGEN_DRP_DI[11], i0.CLKGEN_DRP_DI[10], i0.CLKGEN_DRP_DI[9], i0.CLKGEN_DRP_DI[8], i0.CLKGEN_DRP_DI[7], i0.CLKGEN_DRP_DI[6], i0.CLKGEN_DRP_DI[5], i0.CLKGEN_DRP_DI[4], i0.CLKGEN_DRP_DI[3], i0.CLKGEN_DRP_DI[2], i0.CLKGEN_DRP_DI[1], i0.CLKGEN_DRP_DI[0]};
                13 : bus_if_rd_data <= '{i0.CLKGEN_DRP_DO[15], i0.CLKGEN_DRP_DO[14], i0.CLKGEN_DRP_DO[13], i0.CLKGEN_DRP_DO[12], i0.CLKGEN_DRP_DO[11], i0.CLKGEN_DRP_DO[10], i0.CLKGEN_DRP_DO[9], i0.CLKGEN_DRP_DO[8], i0.CLKGEN_DRP_DO[7], i0.CLKGEN_DRP_DO[6], i0.CLKGEN_DRP_DO[5], i0.CLKGEN_DRP_DO[4], i0.CLKGEN_DRP_DO[3], i0.CLKGEN_DRP_DO[2], i0.CLKGEN_DRP_DO[1], i0.CLKGEN_DRP_DO[0]};
                14 : bus_if_rd_data <= '{1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0, i0.CLKGEN_DRP_DEN, i0.CLKGEN_DRP_WR_EN, i0.CLKGEN_DRP_RD_EN};
                default: bus_if_rd_data <= 'd0;
            endcase
        end else
            bus_if_rd_data <= '0;
    end
endmodule

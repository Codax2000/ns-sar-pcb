interface reg_if;
    logic [13:0] NFFT_POWER;
    logic        DWA_EN;
    logic [7:0] OSR_POWER;
    logic [15:0] N_SH_TOTAL_CYCLES;
    logic [15:0] N_SH_ACTIVE_CYCLES;
    logic [15:0] N_BOTTOM_PLATE_ACTIVE_CYCLES;
    logic [15:0] N_SAR_CYCLES;
    logic [15:0] N_INT1_TOTAL_CYCLES;
    logic [15:0] N_INT1_ACTIVE_CYCLES;
    logic [15:0] N_INT2_TOTAL_CYCLES;
    logic [15:0] N_INT2_ACTIVE_CYCLES;
    logic        START_CONVERSION;
    logic        START_CONVERSION_set;
    logic        START_CONVERSION_clear;
    logic [2:0] MAIN_STATE_RB;
    logic [6:0] CLKGEN_DRP_DADDR;
    logic [15:0] CLKGEN_DRP_DI;
    logic [15:0] CLKGEN_DRP_DO;
    logic        CLKGEN_DRP_RD_EN;
    logic        CLKGEN_DRP_WR_EN;
    logic        CLKGEN_DRP_DEN;

    modport RD (
        input NFFT_POWER,
        input DWA_EN,
        input OSR_POWER,
        input N_SH_TOTAL_CYCLES,
        input N_SH_ACTIVE_CYCLES,
        input N_BOTTOM_PLATE_ACTIVE_CYCLES,
        input N_SAR_CYCLES,
        input N_INT1_TOTAL_CYCLES,
        input N_INT1_ACTIVE_CYCLES,
        input N_INT2_TOTAL_CYCLES,
        input N_INT2_ACTIVE_CYCLES,
        input START_CONVERSION,
        input MAIN_STATE_RB,
        input CLKGEN_DRP_DADDR,
        input CLKGEN_DRP_DI,
        input CLKGEN_DRP_DO,
        input CLKGEN_DRP_RD_EN,
        input CLKGEN_DRP_WR_EN,
        input CLKGEN_DRP_DEN
    );

    modport WR_SYS_CLK (
        output NFFT_POWER,
        output DWA_EN,
        output OSR_POWER,
        output N_SH_TOTAL_CYCLES,
        output N_SH_ACTIVE_CYCLES,
        output N_BOTTOM_PLATE_ACTIVE_CYCLES,
        output N_SAR_CYCLES,
        output N_INT1_TOTAL_CYCLES,
        output N_INT1_ACTIVE_CYCLES,
        output N_INT2_TOTAL_CYCLES,
        output N_INT2_ACTIVE_CYCLES,
        output START_CONVERSION,
        output CLKGEN_DRP_DADDR,
        output CLKGEN_DRP_DI,
        output CLKGEN_DRP_RD_EN,
        output CLKGEN_DRP_WR_EN,
        output CLKGEN_DRP_DEN,
        input MAIN_STATE_RB,
        input CLKGEN_DRP_DO
    );

    modport WR_BUS_CLK (
        output MAIN_STATE_RB,
        output CLKGEN_DRP_DO,
        input NFFT_POWER,
        input DWA_EN,
        input OSR_POWER,
        input N_SH_TOTAL_CYCLES,
        input N_SH_ACTIVE_CYCLES,
        input N_BOTTOM_PLATE_ACTIVE_CYCLES,
        input N_SAR_CYCLES,
        input N_INT1_TOTAL_CYCLES,
        input N_INT1_ACTIVE_CYCLES,
        input N_INT2_TOTAL_CYCLES,
        input N_INT2_ACTIVE_CYCLES,
        input START_CONVERSION,
        input CLKGEN_DRP_DADDR,
        input CLKGEN_DRP_DI,
        input CLKGEN_DRP_RD_EN,
        input CLKGEN_DRP_WR_EN,
        input CLKGEN_DRP_DEN
    );

    modport WR_MAIN_STATE_RB (output MAIN_STATE_RB);
    modport WR_CLKGEN_DRP_DO (output CLKGEN_DRP_DO);

    modport CLEAR_START_CONVERSION (output START_CONVERSION_clear);

endinterface

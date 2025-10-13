module dig_core #(
    parameter N_SAR_BITS = 3
) (
    // clkgen pins
    input logic i_sysclk,
    input logic i_sysrst_b,
    
    // analog boundary pins
    input logic i_sar_compare,
    output logic [(2<<N_SAR_BITS)-1:0] o_caps_to_vin,
    output logic [(2<<N_SAR_BITS)-1:0] o_caps_to_vcm,
    output logic [(2<<N_SAR_BITS)-1:0] o_caps_to_vdd,
    output logic [(2<<N_SAR_BITS)-1:0] o_caps_to_vss,
    output logic o_integrator_1,
    output logic o_integrator_2,
    output logic o_sample,
    // TODO: connect bottom plates
    // TODO: connect analog boundary pins to status interface for verification in the scoreboard
    
    // SPI IO pins
    input logic i_cs_b,
    input logic i_scl,
    input logic i_mosi,
    output logic o_miso
);

    localparam DATA_WIDTH = 16;
    localparam ADDR_WIDTH = 15;

    // system signals from clock gen and reset IP
    logic pll_clk;
    logic pll_is_locked;
    logic sys_rst_b;
    logic sys_rst;

    // bus interface registers
    logic [DATA_WIDTH-1:0] reg_wr_data;
    logic [DATA_WIDTH-1:0] reg_rd_data;
    logic [ADDR_WIDTH-1:0] reg_addr;
    logic                  reg_rd_en;
    logic                  reg_wr_en;
    logic [DATA_WIDTH-1:0] mem_rd_data;
    logic [DATA_WIDTH-1:0] spi_rd_data;
    
    reg_if                 i_reg_if_spi_clk ();
    reg_if                 i_reg_if_sys_clk ();

    spi #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) i_spi (
        .scl(i_scl),
        .mosi(i_mosi),
        .miso(o_miso),
        .cs_b(i_cs_b || (!sys_rst_b)), // hold SPI in reset if the device is in reset

        .reg_wr_data,
        .reg_rd_data,
        .reg_addr,
        .reg_rd_en,
        .reg_wr_en
    );

    data_mem i_adc_mem (
        .clkb(i_scl),
        .addr_b(reg_addr),
        .rd_data_b(mem_rd_data)
    );

    registers i_registers (
        .i0(i_reg_if_spi_clk),
        .clk(i_scl),
        .rst_b(sys_rst_b), // connect to system reset, not anything from SPI
        .bus_if_wr_addr(reg_addr),
        .bus_if_wr_data(reg_wr_data),
        .bus_if_wr_en(reg_wr_en),
        .bus_if_rd_addr(reg_addr),
        .bus_if_rd_data(reg_rd_data),
        .bus_if_rd_en(reg_rd_en)
    );

    main_state_machine #(
        .N_SAR_BITS(N_SAR_BITS)
    ) i_main_state_machine (
        .rd(i_reg_if_sys_clk),
        .i_clk(pll_clk),
        .i_rst_b(sys_rst_b),
        .i_start(!i_reg_if_sys_clk.START_CONVERSION),
        .o_main_state(i_reg_if_sys_clk.MAIN_STATE_RB),

    )

    cdc_sync #(
        .N_SYNC_STAGES(3)
    ) i_cdc_sync (
        .bus_clk_reg(i_reg_if_spi_clk.WR_BUS_CLK),
        .sys_clk_reg(i_reg_if_sys_clk.WR_SYS_CLK),
        .sys_clk(pll_clk),
        .bus_clk(i_scl)
    );

    assign spi_rd_data = reg_addr[ADDR_WIDTH-1] ? mem_rd_data : reg_rd_data;

    clk_gen_xip i_clk_gen (
        .reset(sys_rst),
        .clk_in1(i_sysclk),
        .clk_out1(pll_clk),
        .locked(pll_is_locked),
        .daddr(i_reg_if_sys_clk.CLKGEN_DRP_DADDR),
        .dwe(i_reg_if_sys_clk.CLKGEN_DRP_WR_EN),
        .den(i_reg_if_sys_clk.CLKGEN_DRP_DEN),
        .din(i_reg_if_sys_clk.CLKGEN_DRP_DI),
        .dout(i_reg_if_sys_clk.CLKGEN_DRP_DO)
    );

    reset_gen_xip i_reset_gen (
        .slowest_sync_clk(i_sysclk),
        .ext_reset_in(i_sysrst_b),

        .dcm_locked(1'b1),
        .aux_reset_in(1'b1),
        .mb_debug_sys_rst(1'b0),

        .peripheral_reset(sys_rst)
    );
    assign sys_rst_b = (!sys_rst) && pll_is_locked;

    // TEMPORARY
    assign i_reg_if_spi_clk.START_CONVERSION_clear = 1'b0;
    assign i_reg_if_sys_clk.START_CONVERSION_set = 1'b0;
    assign i_reg_if_spi_clk.START_CONVERSION_set = 1'b0;

endmodule
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
    
    // SPI IO pins
    input logic i_cs_b,
    input logic i_scl,
    input logic i_mosi,
    output logic o_miso
);

    localparam DATA_WIDTH = 16;
    localparam ADDR_WIDTH = 15;

    // internal wires
    logic start_sar_conversion;
    logic sar_conversion_done;

    logic [ADDR_WIDTH-1:0] rd_addr;
    logic [DATA_WIDTH-1:0] memory_data;

    logic [ADDR_WIDTH-1:0] wr_addr;
    logic [DATA_WIDTH-1:0] write_data;
    logic                  wr_en;

    // conversion-side variables
    logic       dwa;
    logic [3:0] nfft_power, clk_div;
    logic [2:0] osr_power;
    logic [1:0] fsm_status_sysclk, fsm_status_spiclk;

    // conversion-start signals
    logic start_conversion;
    logic sm_ready;
    logic fifo_is_empty;

    // system signals from IP
    logic pll_clk;
    logic pll_is_locked;
    logic sys_rst_b;
    logic sys_rst;

    if_reg i_if_reg (.i_clk(i_scl), .i_rst_b(i_sysrst_b));

    spi #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) i_spi (
        .i_scl,
        .i_csb(i_cs_b),
        .i_mosi,
        .o_miso,

        .o_start_coversion(start_conversion),
        .i_fsm_status(fsm_status_spiclk),

        .o_rd_addr(rd_addr),
        .i_memory_data(memory_data),
    
        .i_if_reg(i_if_reg)
    );

    registers i_reg (i_if_reg);

    cdc_sync cdc (
        .i_dwa       (i_if_reg.dwa),
        .i_osr_power (i_if_reg.osr_power),
        .i_nfft_power(i_if_reg.nfft_power),
        .i_clk_div   (i_if_reg.clk_div),

        .o_dwa(dwa),
        .o_nfft_power(nfft_power),
        .o_clk_div(clk_div),
        .o_osr_power(osr_power),

        .o_fsm_status(fsm_status_spiclk),

        .i_clk_spi(i_scl),
        .i_clk_sys(pll_clk)
    );

    clk_gen i_clk_gen (
        .reset(sys_rst),
        .clk_in1(i_sysclk),
        .clk_out1(pll_clk),
        .locked(pll_is_locked)
    );

    data_mem i_data_mem (
        .clka(pll_clk),
        .addr_a(wr_addr),
        .wr_data_a(write_data),
        .wr_enable_a(wr_en),

        .clkb(i_scl),
        .addr_b(rd_addr),
        .rd_data_b(memory_data)
    );

    main_state_machine i_main_state_machine (
        .i_arst_b(sys_rst_b),
        .i_clk(pll_clk),

        .o_ready(sm_ready),
        .i_start((!fifo_is_empty) && pll_is_locked),

        .o_start_coversion(start_sar_conversion),
        .i_conversion_done(sar_conversion_done)
    );

    fifo i_conversion_fifo (
        .rst(sys_rst_b),
        .rd_clk(pll_clk),
        .wr_clk(i_scl),

        .wr_en(start_conversion),
        .din(start_conversion),

        .rd_en(!fifo_is_empty && sm_ready && pll_is_locked),
        .empty(fifo_is_empty)
    );

    reset_gen i_reset_gen (
        .slowest_sync_clk(i_sysclk),
        .ext_reset_in(i_sysrst_b),

        .dcm_locked(1'b1),
        .aux_reset_in(1'b1),
        .mb_debug_sys_rst(1'b0),

        .peripheral_reset(sys_rst)
    );
    assign sys_rst_b = !sys_rst;

    // temporary, in lieu of SAR logic
    assign fsm_status_sysclk[0] = sm_ready;
    assign fsm_status_sysclk[1] = 1'b0;
    assign sar_conversion_done  = 1'b1;

endmodule
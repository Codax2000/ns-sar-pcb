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

    logic [15:0] temp_data;
    always_ff @(posedge i_scl or posedge i_cs_b) begin
        if (i_cs_b)
            temp_data <= 0;
        else begin
            if (reg_rd_en)
                temp_data <= 16'hABBA;
            else
                temp_data <= 0;
        end
    end

    spi #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) i_spi (
        .scl(i_scl),
        .mosi(i_mosi),
        .miso(o_miso),
        .cs_b(i_cs_b && sys_rst_b), // hold SPI in reset if the device is in reset

        .reg_wr_data,
        .reg_rd_data(temp_data),
        .reg_addr,
        .reg_rd_en,
        .reg_wr_en,

        .en_addr_auto_adjust(1'b1) // TODO: add register value
    );

    clk_gen_xip i_clk_gen (
        .reset(sys_rst),
        .clk_in1(i_sysclk),
        .clk_out1(pll_clk),
        .locked(pll_is_locked)
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

endmodule
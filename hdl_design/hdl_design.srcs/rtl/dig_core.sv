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
    localparam ADDR_WIDTH = 4;

    // internal wires
    logic start_conversion;

    logic [ADDR_WIDTH-1:0] rd_addr;
    logic [DATA_WIDTH-1:0] memory_data;
    assign memory_data = !rd_addr[0] ? 16'hCAFE : 16'hFEED ;

    if_reg i_if_reg (.i_clk(i_scl), .i_rst_b(i_cs_b));

    spi #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) i_spi (
        .i_scl,
        .i_csb(i_cs_b),
        .i_mosi,
        .o_miso,

        .o_start_coversion(start_conversion),

        .o_rd_addr(rd_addr),
        .i_memory_data(memory_data),
    
        .i_if_reg(i_if_reg)
    );

    registers i_reg (i_if_reg);

endmodule
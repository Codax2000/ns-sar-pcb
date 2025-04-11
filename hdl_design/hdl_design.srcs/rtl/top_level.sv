module top_level #(
    parameter N_SAR_BITS=3
) (
    input logic i_sar_compare,
    input logic i_sysclk,
    input logic i_sysrst_b,
    output logic [2^N_SAR_BITS-1:0] o_caps_to_vin,
    output logic [2^N_SAR_BITS-1:0] o_caps_to_vcm,
    output logic [2^N_SAR_BITS-1:0] o_caps_to_vdd,
    output logic [2^N_SAR_BITS-1:0] o_caps_to_vss,
    output logic o_integrator_1,
    output logic o_integrator_2,
    output logic o_sample,
    
    // SPI IO pins
    input logic i_cs_b,
    input logic i_scl,
    input logic i_mosi,
    output logic o_miso
);

endmodule
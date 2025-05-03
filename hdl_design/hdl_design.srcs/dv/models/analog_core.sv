/**
models the analog frontend of the SAR IADC, using the same inputs as the
board will have. There are 5 control signals, differential inputs, and
capacitor control switches. It is assumed that nonoverlapping clocks and
bootstrapping switches are implemented on board using discrete components.
*/

module analog_frontend #(
    parameter real VDD=3.3,
    parameter N_QUANTIZER_BITS=3
) (
    // sampling inputs
    if_input.hardware_port signal_in,

    // control signals
    if_analog_to_fpga #(.N_QUANTIZER_BITS(N_QUANTIZER_BITS)) if_digital
);

    localparam real VCM = VDD / 2;
    localparam real VSS = 0;

    real vip_sample, vin_sample;
    real i1p, i1n, i1p_r, i1n_r;
    real i2p, i2n, i2p_r, i2n_r;
    real vresp, vresn;
    real vintp, vintn;
    real [2**N_QUANTIZER_BITS-1:0] cap_voltages_p, cap_voltages_n;

    always_ff @(posedge if_digital.sample) begin
        vip_sample <= VDD - signal_in.vip;
        vin_sample <= VDD - signal_in.vin;
    end

    assign i1p = i1p_r + vresp;
    assign i1n = i1n_r + vresn;
    always_ff @(posedge if_digital.integrate_1 or posedge i_reset_integrators) begin
        if (i_reset_integrators) begin
            i1p_r <= VCM;
            i1n_r <= VCM;
        end else begin
            i1p_r <= i1p;
            i1n_r <= i1n;
        end
    end

    assign i2p = i1p_r + i2p_r;
    assign i2n = i1n_r + i2n_r;
    always_ff @(posedge if_digital.integrate_2 or posedge i_reset_integrators) begin
        if (i_reset_integrators) begin
            i2p_r <= VCM;
            i2n_r <= VCM;
        end else begin
            i2p_r <= i2p;
            i2n_r <= i2n;
        end
    end

    assign vresp = sum_real_array(cap_voltages_p) / (2**N_QUANTIZER_BITS) + vip_sample;
    assign vresn = sum_real_array(cap_voltages_n) / (2**N_QUANTIZER_BITS) + vin_sample;
    assign vintp = 2 * i1p_r + i2p_r;
    assign vintn = 2 * i1n_r + i2n_r;
    assign if_digital.compare = vintp + vresn >= vintn + vresp;

    genvar i;
    for (i = 0; i < 2**N_QUANTIZER_BITS; i++) begin : gen_capacitor_switch_mux
        assign cap_voltages_p[i] =  i_cap_set[i] ? 
                                        i_cap_p_voltages[i] ? VDD : VSS
                                    : VCM;
        assign cap_voltages_n[i] =  i_cap_set[i] ? 
                                        !i_cap_p_voltages[i] ? VDD : VSS
                                    : VCM;
    end
endmodule

function real sum_real_array(array);
    real array_sum = 0;
    foreach (array[i]) begin
        array_sum = array_sum + array[i]
    end
    return array_sum;
endfunction
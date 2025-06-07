interface if_analog_to_fpga #(
    parameter N_QUANTIZER_BITS=3
);

    logic sample;
    logic en_sar;
    logic integrate_1;
    logic integrate_2;
    logic reset_integrators;
    
    // capacitor controls
    logic [2**N_QUANTIZER_BITS-1:0] cap_set;
    logic [2**N_QUANTIZER_BITS-1:0] cap_p_voltages;

    // comparator output to FPGA
    logic compare;

endinterface
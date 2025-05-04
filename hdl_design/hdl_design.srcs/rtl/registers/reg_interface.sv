interface reg_interface;

    logic [3:0] nfft_power;
    logic do_dwa;
    logic [2:0] osr_power;
    logic [3:0] sampclk_div;

    modport clock_div (
        input sampclk_div
    );

    modport sar_registers (
        input nfft_power, do_dwa, osr_power
    )

endinterface
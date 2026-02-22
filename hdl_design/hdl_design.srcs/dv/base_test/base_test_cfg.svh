/**
Class: base_test_cfg

Container class for all configuration items not coming from the hardware toplevel.
They control test-level items such as clock frequencies, reset pulse duration,
and coverage/SVA checking.
*/
class base_test_cfg extends uvm_object;

    `uvm_object_utils(base_test_cfg)

    function new (string name = "base_test_cfg");
        super.new(name);
    endfunction

    // Variable: checks_enable
    // If 1, enables any defined internal SVA checks on the agents.
    bit checks_enable;

    // Variable: coverage_enable
    // If 1, enables building and collection of any coverage defined by the agents or the env.
    bit coverage_enable;

    // Variable: spi_clk_frequency
    // Frequency in *Hz* that the SPI clock must run at. 10 kHz probably good for implementation,
    // 2 MHz good for early simulation.
    real spi_clk_frequency;

    // Variable: system_clk_frequency
    // The frequency in *Hz* that the system clock must run at. Eventually, set to be the same
    // speed as they PCB oscillator and assume an internal PLL, so maybe 5-12 MHz is good.
    real system_clk_frequency;

    // Variable: reset_duration
    // The duration in seconds that the reset pulse will last at the start of simulation.
    real reset_duration;

endclass
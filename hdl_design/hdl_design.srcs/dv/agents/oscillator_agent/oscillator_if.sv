`timescale 1ns/1fs

/**
Interface: oscillator_if

Interface for frequency detection. Contains internal variables for clock
enabled and current observed frequency that should be used for any monitor.
*/
interface oscillator_if;

    // Group: Driver Values
    // Defines values and functions intended for use by the UVM driver.

    // Variable: clk_driven
    // The clock driven to the DUT.
    bit clk_driven;

    // Variable: clk_enable_driven
    // When 1, <clk_driven> will be set to begin oscillating.
    bit clk_enable_driven;

    // Variable: frequency_driven
    // A utility variable used by the sine bridge and set in <start_clock>.
    real frequency_driven;

    // Variable: disabled_state_driven
    // The disabled state that the clock will use when not oscillating
    bit disabled_state_driven;

    real delay_ns;

    // Function: start_clock
    // Allows the user to start the clock going to the DUT with the given
    // frequency.
    //
    // Parameters:
    //   frequency - the frequency in Hz with which to drive the clock
    task start_clock(real frequency);
        stop_clock(0);
        delay_ns = (1e9 / (frequency * 2.0));
        clk_enable_driven = 1;
        frequency_driven = frequency;
        fork
            begin
                while (clk_enable_driven) begin
                    #(delay_ns);
                    if (clk_enable_driven)
                        clk_driven = !clk_driven;
                end
                clk_driven = disabled_state_driven;
            end
        join_none
    endtask

    // Function: stop_clock
    // Stop the output clock with the given disabled state.
    task stop_clock(bit disabled_state);
        disabled_state_driven = disabled_state;
        clk_enable_driven = 0;
        clk_driven = disabled_state;
    endtask

    // Group: Monitor Values
    // Defines values and functions intended for use by the UVM monitor.

    // Variable: clk_observed
    // The observed clock from the DUT
    bit clk_observed;

    // Variable: frequency_observed
    // The observed frequency from the DUT
    real frequency_observed;
    
    // Variable: timeout_time_ns
    // The amount of time in ns before which a timeout shall be registered
    int timeout_time_ns;
    int timeout_count;
    
    // Variable: clk_enable_observed
    // Whether the observed clock is believed to be enabled or disabled
    bit clk_enable_observed;

    // Variable: disabled_state_observed
    // The observed disabled state of the disabled clock
    bit disabled_state_observed;
    assign disabled_state_observed = clk_enable_observed ? 0 : clk_observed;
    
    real time_0;
    real time_1;

    initial time_0 = 0.0;
    initial time_1 = 0.0;

    always @(clk_observed) begin : calc_observed_frequency
        time_1 = $realtime() * 1e-9; // convert time to seconds from ns
        frequency_observed <= 1 / (2 * (time_1 - time_0));
        if ((time_1 - time_0) < timeout_time_ns) begin
            timeout_count <= 0;
            clk_enable_observed <= 1;
        end
        time_0 <= time_1;
    end

    initial begin
        timeout_count <= 0;
        forever begin
            #1ns;
            if (timeout_count < timeout_time_ns) begin
                timeout_count++;
                if (timeout_count == timeout_time_ns)
                    clk_enable_observed <= 0;
            end
        end
    end

endinterface


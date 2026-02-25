`timescale 1ns/1fs
/**
Module: sine_ms_bridge_core

Converts differential signals to single-ended.
*/
module sine_ms_bridge_core #(
    parameter DEFAULT_AMPLITUDE = 0.5,
    parameter DEFAULT_POINTS_PER_PERIOD = 48
) (
    input real vdd,
    input real vss,

    output real voutp,
    output real voutn,

    input real vinp,
    input real vinn,

    output logic clk_observed,

    input logic clk_driven,
    input bit clk_enabled
);
    localparam real PI = 3.14159;

    // Group: Driver

    // Variable: amplitude_driven
    // The amplitude that will be driven onto the net.
    real amplitude_driven = DEFAULT_AMPLITUDE;

    // Variable: points_per_period
    // The number of points driven per period of the oscillation; effectively
    // sets the precision of the driver. More points -> smaller timestep and more precision.
    int points_per_period = DEFAULT_POINTS_PER_PERIOD;

    // Variable: phase
    // The current phase that is being driven
    real phase;

    // Variable: frequency
    // The current frequency that is being driven
    real frequency;

    initial frequency = 1.0;

    real current_delay_ns = 1.0;
    real phase_increase;
    always @(frequency or points_per_period) begin
        current_delay_ns = 1e9 / (frequency * points_per_period);
        phase_increase = (PI) / (0.5 * points_per_period);
    end

    initial begin
        phase = 0.0;
        forever begin
            #(current_delay_ns);
            phase += (phase_increase);
        end
    end

    always @(clk_driven) begin : sync_with_input_clock
        if (clk_driven)
            phase = 0.0;
        else
            phase = PI;
    end

    always @(posedge clk_enabled)
        phase = 0.0;

    assign voutp = clk_enabled ? ((vdd + vss) / 2.0) + amplitude_driven * $sin(phase) : 
                   clk_driven  ? ((vdd + vss) / 2.0) + amplitude_driven * (vdd - vss) : 
                                 ((vdd + vss) / 2.0) - amplitude_driven * (vdd - vss);
    assign voutn = vdd - voutp;

    int voutp_int;
    int voutn_int;
    int phase_int;
    assign voutp_int = int'(voutp * 2048.0);
    assign voutn_int = int'(voutn * 2048.0);
    assign phase_int = int'(phase * 2048.0);

    // Group: Monitor
    // These are signals that are intended to be used by the proxy to signal values to the monitor.

    // Variable: amplitude_observed
    // The amplitude that is observed at the input; that is, the amplitude that is believed
    // to be the current received one.
    real amplitude_observed;

    // Variable: differential
    // Signal used by the monitor to know when an update to the amplitude is available. Cleared
    // automatically when the differential changes, i.e. when the monitor should be done sampling.
    real differential;

    real previous_amplitude;

    always @(vinp or vinn) begin
        differential <= (vinp - vinn) - previous_amplitude;
        previous_amplitude <= vinp - vinn;
    end

    bit    differential_gt_0;
    assign differential_gt_0 = differential > 0;

    always @(differential_gt_0) begin
        amplitude_observed <= vinp > vinn ? (vinp - vinn) - differential : 
                                           (vinn - vinp) - differential;
    end
    assign clk_observed = vinp > vinn;

endmodule
`timescale 1ns/1ns

interface if_input ();

    real vip;
    real vin;
    real phase;
    real frequency;
    real amplitude;
    int delta_t = 1; // 1 ns sample rate
    localparam PI = 3.14159;

    modport hardware_port (input vip, vin);

    always begin
        vip <= $cos(phase * 2 * PI) * amplitude;
        vin <= -1 * $cos(phase * 2 * PI) * amplitude;
        #delta_t;
    end

    always begin
        #delta_t;
        if (frequency != 0)
            phase += frequency * delta_t * 1e-9;
        else
            phase = 0;

    end

    initial begin
        phase = 0;
        amplitude = 0;
    end

endinterface
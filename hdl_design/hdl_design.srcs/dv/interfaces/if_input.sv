`timescale 1ns/1ps

interface if_input ();

    real vip;
    real vin;

    real phase;
    real frequency;
    real amplitude;
    real vcm;

    localparam PI = 3.14159;
    bit values_changed;

    modport hardware_port (input vip, input vin);

    initial begin
        vcm = 0;
        phase = 0;
        values_changed = 1'b0;
        forever begin
            #1;
            if (frequency != 0)
                phase += frequency * 1e-9;
            else
                phase = 0;
            vip <= vcm + $cos(phase * 2 * PI) * amplitude / 2;
            vin <= vcm - $cos(phase * 2 * PI) * amplitude / 2;
        end
    end

endinterface
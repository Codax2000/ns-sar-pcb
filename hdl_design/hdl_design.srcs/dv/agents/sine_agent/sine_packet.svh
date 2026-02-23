/**
Class: sine_packet

Extension of <oscillator_packet> intended to be used to drive a sine wave.
*/
class sine_packet extends oscillator_packet;

    // Variable: amplitude
    // Represents the amplitude of the sine wave as a fraction of VDD. Must
    // not be greater than 0.5, and must be greater than 0.0.
    real amplitude;

    rand int amplitude_int;

    constraint legal_amplitude {
        amplitude_int <= 1024;

        if (enabled)
            amplitude_int >= 1;
        else
            amplitude_int >= 0; // disabled clock can have 0 amplitude
    }

    `uvm_object_utils_begin(sine_packet)
        `uvm_field_real(amplitude, UVM_ALL_ON)
    `uvm_object_utils_end

    function new (string name = "sine_packet");
        super.new(name);
    endfunction

    function void post_randomize();
        super.post_randomize();
        this.amplitude = amplitude_int / 2048.0;
    endfunction

endclass
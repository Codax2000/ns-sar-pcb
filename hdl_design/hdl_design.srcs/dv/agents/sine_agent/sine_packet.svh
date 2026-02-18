/**
Class: sine_packet

Extension of <oscillator_packet> intended to be used to drive a sine wave.
*/
class sine_packet extends oscillator_packet;

    // Variable: amplitude
    // Represents the amplitude of the sine wave as a fraction of VDD. Must
    // not be greater than 0.5, and must be greater than 0.0.
    rand real amplitude;

    constraint legal_amplitude {
        amplitude <= 0.5;
        amplitude > 0.0;
    }

    `uvm_object_utils_begin(sine_packet)
        `uvm_field_real(amplitude, UVM_ALL_ON)
    `uvm_object_utils_end

    function new (string name = "sine_packet");
        super.new(name);
    endfunction

endclass
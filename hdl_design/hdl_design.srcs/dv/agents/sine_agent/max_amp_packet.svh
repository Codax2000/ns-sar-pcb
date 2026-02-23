/**
Class: max_amp_packet

Extension of the sine packet that forces max amplitude.
*/
class max_amp_packet extends sine_packet;

    `uvm_object_utils(max_amp_packet)

    function new(string name = "max_amp_packet");
        super.new(name);
    endfunction

    constraint max_amplitude {
        amplitude_int == 1024;
    }

endclass
/**
Class: oscillator_packet

Represents the current state of an oscillator; frequency, enabled status, and
disabled state.
*/
class oscillator_packet extends uvm_sequence_item;

    // Variable: enabled
    // If 1, the clock is enabled with the given frequency. Else, the clock is
    // disabled with the packet disabled state.
    rand bit enabled;

    // Variable: frequency
    // Determines the frequency of an active clock
    rand real frequency;

    // Variable: disabled_state
    // Determines the disabled state of an inactive clock
    rand bit disabled_state;

    `uvm_object_utils_begin(oscillator_packet)
        `uvm_field_int(enabled, UVM_ALL_ON)
        `uvm_field_real(frequency, UVM_ALL_ON)
        `uvm_field_int(disabled_state, UVM_ALL_ON)
    `uvm_object_utils_end

    function new(string name = "oscillator_packet");
        super.new(name);
    endfunction

    constraint default_frequency_range {
        frequency <= 1e9;
        frequency >= 100.0;
    }

endclass
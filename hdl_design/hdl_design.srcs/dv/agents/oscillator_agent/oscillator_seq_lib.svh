/**
Class: oscillator_single_packet_seq

Represents a single oscillator packet. Randomizes a single packet with the
sequence enable state, frequency, and disabled state.
*/
class oscillator_single_packet_seq extends uvm_sequence #(oscillator_packet);

    // Variable: enabled
    // If 1, the clock is enabled with the given frequency. Else, the clock is
    // disabled with the packet disabled state.
    rand bit pkt_enabled;

    // Variable: frequency
    // Determines the frequency of an active clock
    rand real pkt_frequency;

    // Variable: disabled_state
    // Determines the disabled state of an inactive clock
    rand bit pkt_disabled_state;

    `uvm_object_utils_begin(oscillator_single_packet_seq)
        `uvm_field_int(enable)
        `uvm_field_real(frequency)
        `uvm_field_int(disabled_state)
    `uvm_object_utils_end

    constraint default_frequency_range {
        frequency <= 1e9;
        frequency >= 100.0;
    }

    function new (string name = "single_packet_seq");
        super.new(name);
    endfunction

    virtual task body();
        oscillator_packet pkt;

        pkt = oscillator_packet::type_id::create("pkt");

        pkt.randomize() with {
            enabled == pkt_enabled;
            frequency == pkt_frequency;
            disabled_state == pkt_disabled_state;
        };

        start_item(pkt);
        finish_item(pkt);
    endtask

endclass
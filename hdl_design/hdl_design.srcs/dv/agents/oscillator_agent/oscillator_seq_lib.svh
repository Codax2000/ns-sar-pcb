/**
Class: oscillator_single_packet_seq

Represents a single oscillator packet. Randomizes a single packet with the
sequence enable state, frequency, and disabled state.
*/
class oscillator_single_packet_seq extends uvm_sequence #(oscillator_packet);

    // Variable: pkt_enabled
    // If 1, the clock is enabled with the given frequency. Else, the clock is
    // disabled with the packet disabled state.
    rand bit pkt_enabled;

    // Variable: pkt_frequency
    // Determines the frequency of an active clock. Note: this is an integer.
    rand int pkt_frequency;

    // Variable: pkt_disabled_state
    // Determines the disabled state of an inactive clock
    rand bit pkt_disabled_state;

    `uvm_object_utils_begin(oscillator_single_packet_seq)
        `uvm_field_int(pkt_enabled, UVM_ALL_ON)
        `uvm_field_int(pkt_frequency, UVM_ALL_ON)
        `uvm_field_int(pkt_disabled_state, UVM_ALL_ON)
    `uvm_object_utils_end

    constraint default_frequency_range {
        pkt_frequency <= 1000000000;
        pkt_frequency >= 100;
    }

    function new (string name = "single_packet_seq");
        super.new(name);
    endfunction

    virtual task body();
        oscillator_packet pkt;

        pkt = oscillator_packet::type_id::create("pkt");

        pkt.randomize() with {
            enabled == pkt_enabled;
            frequency_int == pkt_frequency;
            disabled_state == pkt_disabled_state;
        };

        start_item(pkt);
        finish_item(pkt);
    endtask

endclass
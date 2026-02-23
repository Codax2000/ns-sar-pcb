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

    // Variable: frequency_int
    // Determines the frequency of an active clock. Just an integer workaround
    // to a real variable set in post_randomize.
    rand int frequency_int;
         real frequency;

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
        frequency_int <= 1000000000;
        frequency_int >= 100;
    }

    function void post_randomize();
        super.post_randomize();
        frequency = real'(frequency_int);
    endfunction

    virtual function bit do_compare (uvm_object rhs, uvm_comparer comparer);
        oscillator_packet rhs_;
            
        if (!$cast(rhs_, rhs)) begin
            `uvm_error("COMPARE", "rhs is not an oscillator_packet")
            return 0;
        end

        
        if (!comparer.compare_field_int("frequency",
                                        this.enabled,
                                        rhs_.enabled,
                                        .size(36)))
            return 0;
        if (rhs_.enabled) begin
            // Compare frequency when enabled
            if (!comparer.compare_field_real("frequency",
                                    this.frequency,
                                    rhs_.frequency))
                return 0;
        end
        else begin
            // Compare disabled_state when disabled
            if (!comparer.compare_field_int("disabled_state",
                                    this.disabled_state,
                                    rhs_.disabled_state,
                                    .size(64)))
                return 0;
        end

        return 1;
    endfunction : do_compare


endclass
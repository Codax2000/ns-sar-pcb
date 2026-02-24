/**
Class: oscillator_coverage_collector

Collects coverage on received packets. By default, crosses frequency with enabled state and
crosses enable with disabled state. Samples coverage on write.
*/
class oscillator_coverage_collector extends uvm_subscriber #(oscillator_packet);

    `uvm_component_utils(oscillator_coverage_collector)

    bit enable;
    int frequency;
    bit disabled_state;

    covergroup oscillator_cov;

        cp_frequency : coverpoint frequency iff (enable) {
            bins low_freq    = {[100 : 999]};
            bins mid_freq    = {[1000   : 999999]};
            bins high_freq   = {[1000000   : 1000000000]};
        }

        cp_disabled_state : coverpoint disabled_state iff (!enable);

    endgroup


    function new (string name, uvm_component parent);
        super.new(name, parent);
        oscillator_cov = new();
    endfunction

    virtual function void write (oscillator_packet t);
        enable = t.enabled;
        frequency = int'(t.frequency);
        disabled_state = t.disabled_state;
        oscillator_cov.sample();
    endfunction

endclass
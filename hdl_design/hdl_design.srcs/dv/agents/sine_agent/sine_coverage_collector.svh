/**
Class: sine_coverage_collector

Collects coverage of amplitude as well as everything else for oscillator coverage.
*/
class sine_coverage_collector extends oscillator_coverage_collector;

    `uvm_component_utils(sine_coverage_collector)

    real amplitude;
    sine_packet pkt;

    covergroup sine_cov;

        cp_frequency : coverpoint frequency iff (enable) {
            bins low_freq    = {[100.0 : 1e3]};
            bins mid_freq    = {[1e3   : 1e6]};
            bins high_freq   = {[1e6   : 1e9]};
        }

        cp_amplitude : coverpoint amplitude iff (enable) {
            bins small_amp  = {[0.0 : 0.1]};
            bins medium_amp = {[0.1 : 0.25]};
            bins large_amp  = {[0.25: 0.5]};
        }

        amp_x_freq : cross cp_frequency, cp_amplitude;

    endgroup

    function new (string name, uvm_component parent);
        super.new(name, parent);
        sine_cov = new();
    endfunction

    virtual function void write(oscillator_packet t);
        super.write(t);

        if ($cast(pkt, t)) begin
            amplitude = pkt.amplitude;
            sine_cov.sample();
        end else
            `uvm_warning(get_full_name(), "Incoming packet is not sine-packet but subscriber is a sine coverage collector. Coverage will not be sampled.")
    endfunction

endclass
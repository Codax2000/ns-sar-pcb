/**
Class: sine_coverage_collector

Collects coverage of amplitude as well as everything else for oscillator coverage.
*/
class sine_coverage_collector extends oscillator_coverage_collector;

    `uvm_component_utils(sine_coverage_collector)

    int amplitude;
    
    sine_packet pkt;

    covergroup sine_cov;

        cp_frequency : coverpoint frequency iff (enable) {
            bins low_freq    = {[100 : 999]};
            bins mid_freq    = {[1000   : 999999]};
            bins high_freq   = {[1000000   : 1000000000]};
        }

        cp_amplitude : coverpoint amplitude {
            bins small_amp  = {[0 : 100]};
            bins medium_amp = {[101 : 512]};
            bins large_amp  = {[513 : 1024]};
        }

        amp_x_freq : cross cp_frequency, cp_amplitude iff (enable);

        amx_x_disable : cross cp_amplitude, disabled_state iff (!enable);

    endgroup

    function new (string name, uvm_component parent);
        super.new(name, parent);
        sine_cov = new();
    endfunction

    virtual function void write(oscillator_packet t);
        super.write(t);

        if ($cast(pkt, t)) begin
            amplitude = int'(2048 * pkt.amplitude);
            sine_cov.sample();
        end else
            `uvm_warning(get_full_name(), "Incoming packet is not sine-packet but subscriber is a sine coverage collector. Coverage will not be sampled.")
    endfunction

endclass
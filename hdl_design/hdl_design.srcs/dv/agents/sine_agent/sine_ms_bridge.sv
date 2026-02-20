/**
Module: sine_ms_bridge

Bridge that converts oscillator inputs to sine waves. Also defines the proxy
necessary for UVM driver and monitor to configure during execution, but parametrized
so as to be able to work without them.

Works with an *internal* oscillator interface, so UVM testbenches will not have
to instantiate them.
*/
module sine_ms_bridge (
    // supply values, used to scale amplitude correctly
    input interconnect vdd,
    input interconnect vss,

    // driven clock, differential with Vcm = vdd / 2
    output interconnect voutp,
    output interconnect voutn,

    // observed clock
    input interconnect vinp,
    input interconnect vinn
);

    oscillator_if bridge_if ();

    class sine_ms_bridge_proxy extends sine_proxy;
        virtual function void configure_driver(input int points_per_period);
            `uvm_ms_info("SINE PROXY", $sformatf("Setting points per period to %0d", points_per_period), UVM_MEDIUM)
            bridge_core.points_per_period = points_per_period;
        endfunction

        virtual function void push(real amplitude);
            if (bridge_if.clk_enable_driven)
                @(bridge_if.clk_driven);
            bridge_core.amplitude_driven = amplitude;
        endfunction

        // Function: sample
        // Blocking sample that makes sure frequency changes if it's going to change
        virtual task sample (output real amplitude);
            if (bridge_if.clk_enable_observed)
                @(bridge_core.differential_gt_0 or bridge_if.clk_enable_observed);
            amplitude = bridge_core.amplitude_observed;
        endtask
    endclass

    sine_ms_bridge_proxy proxy = new();

    always_comb begin
        bridge_core.frequency = bridge_if.frequency_driven;
    end

    always @(bridge_core.amplitude_observed)
        proxy.amplitude = bridge_core.amplitude_observed;

    sine_ms_bridge_core_real bridge_core (
        .vdd,
        .vss,

        .voutp,
        .voutn,

        .vinp,
        .vinn,

        .clk_observed(bridge_if.clk_observed),
        .clk_driven(bridge_if.clk_driven),
        .clk_enabled(bridge_if.clk_enable_driven)
    );
    
endmodule

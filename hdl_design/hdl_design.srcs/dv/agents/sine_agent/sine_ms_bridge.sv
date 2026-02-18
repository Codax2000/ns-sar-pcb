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
        virtual function void push(real amplitude);

        endfunction

        virtual task sample (output real amplitude);
            
        endtask
    endclass

    sine_ms_bridge_proxy proxy = new();

    sine_ms_bridge_core_real (
        .vdd,
        .vss,

        .voutp,
        .voutn,

        .vinp,
        .vinn,

        .clk_observed(bridge_if.clk_observed),
        .clk_driven(bridge_if.clk_driven)
    );
endmodule

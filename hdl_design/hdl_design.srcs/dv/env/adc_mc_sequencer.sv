class adc_mc_sequencer extends uvm_sequencer;

    `uvm_component_utils(adc_mc_sequencer)

    reg_env                     ral;
    uvm_sequencer #(sin_packet) input_sequencer;

    function new(string name = "adc_mc_sequencer", uvm_component parent);
        super.new(name, parent);
    endfunction

endclass
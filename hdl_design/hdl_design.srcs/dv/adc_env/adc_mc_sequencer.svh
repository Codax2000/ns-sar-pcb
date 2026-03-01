/**
Class: adc_mc_sequencer

Class for driving sequences that are used in several places.
*/
class adc_mc_sequencer extends uvm_sequencer;

    `uvm_component_utils(adc_mc_sequencer)

    function new (string name = "adc_mc_sequencer", uvm_component parent);
        super.new(name, parent);
    endfunction

    adc_regs      ral;
    uvm_sequencer #(bit_bus_packet #(1)) m_reset_sequencer;
    uvm_sequencer #(oscillator_packet)   m_clk_sequencer;
    uvm_sequencer #(oscillator_packet)   m_adc_in_sequencer;

    // preloaded sequences
    single_value_seq             reset_seq;
    oscillator_single_packet_seq adc_seq;
    oscillator_single_packet_seq clk_seq;

    virtual function void build_phase(uvm_phase phase);
        reset_seq = single_value_seq #(.WIDTH(1))::type_id::create("reset_seq");
        adc_seq   = oscillator_single_packet_seq::type_id::create("adc_seq");
        clk_seq   = oscillator_single_packet_seq::type_id::create("clk_seq");
    endfunction

endclass
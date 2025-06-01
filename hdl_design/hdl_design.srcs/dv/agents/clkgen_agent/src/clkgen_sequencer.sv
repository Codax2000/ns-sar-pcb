class clkgen_sequencer extends uvm_sequencer #(clkgen_packet);

    `uvm_component_utils(clkgen_sequencer)

    function new (string name = "clkgen_sequencer", uvm_component parent);
        super.new(name, parent);
    endfunction

endclass
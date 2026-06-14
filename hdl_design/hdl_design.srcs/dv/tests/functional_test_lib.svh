/**
Class: ramp_monotonicity_test

Ramps up the input voltage in small increments (at DC, no sine waves)
and reads data back for each one.
*/
class ramp_monotonicity_test extends base_test;

    `uvm_component_utils(ramp_monotonicity_test)

    function new (string name = "ramp_monotonicity_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task main_phase(uvm_phase phase);

        phase.raise_objection(this);



        phase.drop_objection(this);

    endtask

endclass

/**
Class: rand_dc_levels_test

Send random 
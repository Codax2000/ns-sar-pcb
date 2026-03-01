/**
Class: reg_rw_test

Runs UVM predefined sequences on register layer to make sure that
all fields are readable/writeable. This includes RW and bit-banging.
*/
class reg_rw_test extends base_test;

    `uvm_component_utils(reg_rw_test)

    function new (string name = "reg_rw_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task main_phase(uvm_phase phase);
        uvm_reg_hw_reset_seq m_reg_reset_seq;

        phase.raise_objection(this);

        // For each field in address map,
        
        // if field is writeable and is not volatile, randomize it and set()

        // burst update the whole map

        // For each field in address map,
        // read it back and check it

        // Do it again with random bursts (min/max, various sizes)

        phase.drop_objection(this);
    endtask

endclass
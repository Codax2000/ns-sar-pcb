/**
Class: reg_rw_test

Reads and writes all registers single-address and burst reads/writes.
*/
class reg_rw_test extends base_test;

    `uvm_component_utils(reg_rw_test)

    function new (string name = "reg_rw_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task main_phase(uvm_phase phase);
        uvm_sequencer_base   sequencer;
        uvm_status_e         status;

        phase.raise_objection(this);

        `uvm_info(get_full_name(), "Beginning main phase", UVM_LOW)

        regmodel.ADC.SH_CTRL.write(status, 16'h4004);
        regmodel.DAC.ENABLE.dacp_enable.write(status, 1'b1);

        phase.drop_objection(this);
    endtask

endclass

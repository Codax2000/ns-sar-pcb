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
        uvm_reg              m_registers [$];
        uvm_status_e         status;

        phase.raise_objection(this);

        m_env.m_ral.randomize();
        m_env.m_ral.print();
        m_env.burst_update_all_registers();
        m_env.burst_mirror_all_registers(UVM_CHECK);

        m_env.m_ral.randomize();
        m_env.m_ral.update(status);
        
        m_env.m_ral.get_registers(m_registers);
        foreach (m_registers[i]) begin
            m_registers[i].mirror(status, UVM_CHECK);
            if (status != UVM_IS_OK)
                `uvm_error(get_full_name(), $sformatf("Received mirror with status=%s", status.name()))
        end


        phase.drop_objection(this);
    endtask

endclass
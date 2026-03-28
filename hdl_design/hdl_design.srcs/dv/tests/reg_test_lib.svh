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
        uvm_reg_hw_reset_seq m_reg_reset_seq;
        uvm_reg              m_registers [$];
        uvm_status_e         status;

        phase.raise_objection(this);
        
        // check that reset works
        m_env.m_ral.get_registers(m_registers);
        foreach (m_registers[i]) begin
            m_registers[i].mirror(status, UVM_CHECK);
            if (status != UVM_IS_OK)
                `uvm_error(get_full_name(), $sformatf("Received mirror with status=%s", status.name()))
        end

        m_env.m_ral.randomize();
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

/**
Class: main_sm_sar_convert_test

Using a randomized register config with OSR power low and NFFT power low 
(for now) run FFT conversion with no noise shaping. DWA should still be randomized.
*/
class main_sm_sar_convert_test extends base_test;

    `uvm_component_utils(main_sm_sar_convert_test)

    function new(string name = "main_ms_sar_convert_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual task main_phase(uvm_phase phase);
        uvm_reg_data_t data;
        uvm_status_e   status;

        phase.raise_objection(this);

        m_env.m_ral.FFT_CTRL.randomize() with {
            OSR_POWER.value < 4;
            NFFT_POWER.value < 4;
            NOISE_SHAPING_EN.value == 0;
        };

        m_env.m_ral.SH_CTRL.randomize() with {
            N_ACTIVE_CYCLES.value >= 1;
        };

        m_env.m_ral.INT1_CTRL.randomize();
        m_env.m_ral.INT2_CTRL.randomize();
        m_env.m_ral.ADC_CTRL.START_CONVERSION.set(1);

        m_env.burst_update_all_registers();

        do begin
            m_env.m_ral.ADC_CTRL.START_CONVERSION.read(status, data);
            `uvm_info(get_full_name(), $sformatf("Read back value: %h", data), UVM_MEDIUM)
        end while (data == 1);

        phase.drop_objection(this);
    endtask

endclass
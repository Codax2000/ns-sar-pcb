/**
Class: base_test

Instantiates ADC environment and builds up environment config. Child classes
of this test should by default extend main_phase instead of run_phase, since <adc_env> deals with
reset behavior.
*/
class base_test extends uvm_test;

    `uvm_component_utils(base_test)

    // Variable: m_env
    // The toplevel ADC environment that contains agents.
    adc_env       m_env;

    // Variable: m_top_cfg
    // The toplevel configuration object containing virtual interfaces and proxies.
    tb_top_cfg    m_top_cfg;

    // Variable: m_base_test_cfg
    // The base test configuration, controlling non-random values.
    base_test_cfg m_base_test_cfg;

    // Variable: m_env_cfg
    // The environment config; everything needed to create the environment. This includes a mix
    // of elements of <m_top_cfg> and <m_base_test_cfg>.
    adc_env_cfg   m_env_cfg;

    // Variable: vif_status
    // The status interface used to monitor things at the analog-digital boundary.
    // It's entirely possible this will be unused, since everything is achievable through the
    // uvm_hdl_* macros, but could be useful anyway, even if it's empty.
    virtual status_if vif_status;

    function new (string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(tb_top_cfg)::get(this, "*", "tb_top_cfg", m_top_cfg))
            `uvm_fatal("TB_TOP", "Could not attach top-level configuration")
            
        create_configs();

        vif_status = m_top_cfg.vif_status;

        m_env_cfg = adc_env_cfg::type_id::create("m_env_cfg");
        
        m_env_cfg.vif_clk    = m_top_cfg.vif_clk;
        m_env_cfg.vif_reset  = m_top_cfg.vif_reset;
        m_env_cfg.vif_spi    = m_top_cfg.vif_spi;
        m_env_cfg.vif_adc    = m_top_cfg.vif_adc;
        m_env_cfg.vproxy_adc = m_top_cfg.vproxy_adc;

        m_env_cfg.checks_enable        = m_base_test_cfg.checks_enable;
        m_env_cfg.coverage_enable      = m_base_test_cfg.coverage_enable;
        m_env_cfg.spi_clk_frequency    = m_base_test_cfg.spi_clk_frequency;
        m_env_cfg.system_clk_frequency = m_base_test_cfg.system_clk_frequency;
        m_env_cfg.reset_duration       = m_base_test_cfg.reset_duration;
        m_env_cfg.reset_reg_rb_name    = "SYNC_RESET_RB"; // from RDL

        uvm_config_db #(adc_env_cfg)::set(this, "m_env", "cfg", m_env_cfg);

        m_env = adc_env::type_id::create("m_env", this);
    endfunction

    // Function: create_configs
    // Very similar to the ADC environment's <adc_env:create_configs> call. Should
    // be overridden by subclasses to change any test-level configuration values,
    // such as SVA checking on the agent interfaces.
    virtual function void create_configs();
        m_base_test_cfg = base_test_cfg::type_id::create("m_base_test_cfg");

        m_base_test_cfg.checks_enable = 1;
        m_base_test_cfg.coverage_enable = 1;
        m_base_test_cfg.spi_clk_frequency = 2e6; // 2 MHz for now
        m_base_test_cfg.system_clk_frequency = int'(10e6); // 10 MHz crystal oscillator
        m_base_test_cfg.reset_duration = 500e-9; // 500ns reset pulse
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
        uvm_factory::get().print();
    endfunction

    virtual task main_phase(uvm_phase phase);
        uvm_status_e   status;
        uvm_reg_data_t data;
        spi_packet_reg_extension ext;

        phase.raise_objection(this);

        ext = spi_packet_reg_extension::type_id::create("ext");
        ext.additional_write_data.push_back(14);
        ext.additional_write_data.push_back(12);

        m_env.m_ral.INT1_CTRL.N_PASSIVE_CYCLES.write(
            status, 8'hAF, .extension(ext)
        );

        m_env.m_ral.INT1_CTRL.N_PASSIVE_CYCLES.mirror(status, UVM_CHECK);
        m_env.m_ral.INT2_CTRL.N_ACTIVE_CYCLES.mirror(status, UVM_CHECK);
        m_env.m_ral.INT2_CTRL.N_PASSIVE_CYCLES.mirror(status, UVM_CHECK);

        phase.drop_objection(this);
    endtask

endclass
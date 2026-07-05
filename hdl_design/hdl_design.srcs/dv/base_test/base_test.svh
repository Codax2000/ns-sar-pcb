/**
Class: base_test

Instantiates ADC environment and builds up environment config. Child classes
of this test should by default extend main_phase instead of run_phase, since <adc_env> deals with
reset behavior.
*/
class base_test extends uvm_test;

    `uvm_component_utils(base_test)

    // Variable: m_env
    // Top-level RAL model
    chip_top m_chip_ral;

    // Environment configuration objects
    spi_env_cfg #(.REG_BLOCK(adc_regs)) m_adc_spi_env_cfg;
    spi_env_cfg #(.REG_BLOCK(dac_regs)) m_dac_spi_env_cfg;
    spi_agent_cfg m_adc_spi_agent_cfg;
    spi_agent_cfg m_dac_spi_agent_cfg;

    // Environments for different agents
    spi_env #(.REG_BLOCK(adc_regs))      m_adc_spi_env;
    spi_env #(.REG_BLOCK(dac_regs))      m_dac_spi_env;
    bit_bus_agent #(.WIDTH(1))           m_reset_agent;
    oscillator_agent                      m_clk_agent;

    // Variable: m_top_cfg
    // The toplevel configuration object containing virtual interfaces and proxies.
    tb_top_cfg    m_top_cfg;

    // Variable: m_base_test_cfg
    // The base test configuration, controlling non-random values.
    base_test_cfg m_base_test_cfg;

    // Variable: vif_status
    // The status interface used to monitor things at the analog-digital boundary.
    // It\'s entirely possible this will be unused, since everything is achievable through the
    // uvm_hdl_* macros, but could be useful anyway, even if it\'s empty.
    virtual status_if vif_status;

    function new (string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(tb_top_cfg)::get(this, "*", "tb_top_cfg", m_top_cfg))
            `uvm_fatal("TB_TOP", "Could not attach top-level configuration")
            
        create_configs();
        create_spi_configs();

        build_chip_ral();
        assign_spi_env_rals();

        // Set env configs into config_db for spi_env to retrieve
        uvm_config_db #(spi_env_cfg #(adc_regs))::set(this, "m_adc_spi_env", "cfg", m_adc_spi_env_cfg);
        uvm_config_db #(spi_env_cfg #(dac_regs))::set(this, "m_dac_spi_env", "cfg", m_dac_spi_env_cfg);

        // Create agents and environments
        m_reset_agent = bit_bus_agent #(.WIDTH(1))::type_id::create("m_reset_agent", this);
        m_clk_agent = oscillator_agent::type_id::create("m_clk_agent", this);
        m_adc_spi_env = spi_env #(.REG_BLOCK(adc_regs))::type_id::create("m_adc_spi_env", this);
        m_dac_spi_env = spi_env #(.REG_BLOCK(dac_regs))::type_id::create("m_dac_spi_env", this);
    endfunction

    // Function: create_configs
    // Very similar to the ADC environment\'s <adc_env:create_configs> call. Should
    // be overridden by subclasses to change any test-level configuration values,
    // such as SVA checking on the agent interfaces.
    virtual function void create_configs();
        m_base_test_cfg = base_test_cfg::type_id::create("m_base_test_cfg");

        m_base_test_cfg.checks_enable = 1;
        m_base_test_cfg.coverage_enable = 1;
        m_base_test_cfg.spi_clk_frequency = 2e6; // 2 MHz for now
        m_base_test_cfg.system_clk_frequency = int\'(10e6); // 10 MHz crystal oscillator
        m_base_test_cfg.reset_duration = 500e-9; // 500ns reset pulse
    endfunction

    // Function: create_spi_configs
    // Creates and configures the SPI agent and environment configuration objects.
    virtual function void create_spi_configs();
        // ADC SPI Agent Config
        m_adc_spi_agent_cfg = spi_agent_cfg::type_id::create("m_adc_spi_agent_cfg");
        m_adc_spi_agent_cfg.vif = m_top_cfg.vif_adc_spi;
        m_adc_spi_agent_cfg.is_active = UVM_ACTIVE;
        m_adc_spi_agent_cfg.checks_enable = m_base_test_cfg.checks_enable;
        m_adc_spi_agent_cfg.coverage_enable = m_base_test_cfg.coverage_enable;
        m_adc_spi_agent_cfg.clk_speed_hz = m_base_test_cfg.spi_clk_frequency;

        // DAC SPI Agent Config
        m_dac_spi_agent_cfg = spi_agent_cfg::type_id::create("m_dac_spi_agent_cfg");
        m_dac_spi_agent_cfg.vif = m_top_cfg.vif_dac_spi;
        m_dac_spi_agent_cfg.is_active = UVM_ACTIVE;
        m_dac_spi_agent_cfg.checks_enable = m_base_test_cfg.checks_enable;
        m_dac_spi_agent_cfg.coverage_enable = m_base_test_cfg.coverage_enable;
        m_dac_spi_agent_cfg.clk_speed_hz = m_base_test_cfg.spi_clk_frequency;

        // ADC SPI Environment Config
        m_adc_spi_env_cfg = spi_env_cfg #(.REG_BLOCK(adc_regs))::type_id::create("m_adc_spi_env_cfg");
        m_adc_spi_env_cfg.m_spi_agent_cfg = m_adc_spi_agent_cfg;
        m_adc_spi_env_cfg.m_reg_env_cfg = reg_env_cfg #(.REG_BLOCK(adc_regs))::type_id::create("m_adc_reg_env_cfg");

        // DAC SPI Environment Config
        m_dac_spi_env_cfg = spi_env_cfg #(.REG_BLOCK(dac_regs))::type_id::create("m_dac_spi_env_cfg");
        m_dac_spi_env_cfg.m_spi_agent_cfg = m_dac_spi_agent_cfg;
        m_dac_spi_env_cfg.m_reg_env_cfg = reg_env_cfg #(.REG_BLOCK(dac_regs))::type_id::create("m_dac_reg_env_cfg");
    endfunction

    // Function: build_chip_ral
    // Builds the chip-level RAL once at test scope. Subclasses can override to
    // customize construction while keeping assign_spi_env_rals() unchanged.
    virtual function void build_chip_ral();
        m_chip_ral = chip_top::type_id::create("m_chip_ral", this);
        m_chip_ral.build();
        m_chip_ral.lock_model();
        m_chip_ral.reset();
    endfunction

    // Function: assign_spi_env_rals
    // Passes chip_top sub-blocks into each spi_env_cfg. Override to omit a handle
    // (leave null) when an spi_env should build its own standalone register block.
    virtual function void assign_spi_env_rals();
        m_adc_spi_env_cfg.m_reg_env_cfg.m_ral = m_chip_ral.ADC;
        m_dac_spi_env_cfg.m_reg_env_cfg.m_ral = m_chip_ral.DAC;
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Connect virtual interfaces to agents
        uvm_config_db #(virtual bit_bus_if #(.WIDTH(1)))::set(this, "m_reset_agent", "vif", m_top_cfg.vif_reset);
        uvm_config_db #(virtual oscillator_if)::set(this, "m_clk_agent", "vif", m_top_cfg.vif_clk);
        uvm_config_db #(virtual spi_if)::set(this, "m_adc_spi_env.m_spi_agent", "vif", m_top_cfg.vif_adc_spi);
        uvm_config_db #(virtual spi_if)::set(this, "m_dac_spi_env.m_spi_agent", "vif", m_top_cfg.vif_dac_spi);

        // Connect each env's effective RAL map to its SPI sequencer.
        m_adc_spi_env.m_ral.default_map.set_sequencer(
            m_adc_spi_env.m_spi_agent.sequencer,
            m_adc_spi_env.m_reg_env.adapter
        );
        m_dac_spi_env.m_ral.default_map.set_sequencer(
            m_dac_spi_env.m_spi_agent.sequencer,
            m_dac_spi_env.m_reg_env.adapter
        );
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
        uvm_factory::get().print();
        m_chip_ral.print();
    endfunction

    virtual task main_phase(uvm_phase phase);
        uvm_status_e   status;
        // Example usage
        phase.raise_objection(this);
        `uvm_info(get_full_name(), "Starting main_phase", UVM_LOW);

        // Example RAL write to ADC
        m_chip_ral.ADC.SH_CTRL.N_ACTIVE_CYCLES.set(\'h55);
        m_chip_ral.ADC.SH_CTRL.update(status);
        if (status == UVM_NOT_OK) `uvm_error(get_full_name(), "ADC_SH_CTRL write failed");

        // Example RAL write to DAC
        m_chip_ral.DAC.ENABLE.dacp_enable.set(1);
        m_chip_ral.DAC.ENABLE.update(status);
        if (status == UVM_NOT_OK) `uvm_error(get_full_name(), "DAC_ENABLE write failed");

        // Example RAL read from ADC
        m_chip_ral.ADC.CONVERSION_FLAGS.read(status);
        if (status == UVM_NOT_OK) `uvm_error(get_full_name(), "ADC_CONVERSION_FLAGS read failed");
        `uvm_info(get_full_name(), $sformatf("ADC Conversion Flags: 0x%0h", m_chip_ral.ADC.CONVERSION_FLAGS.get()), UVM_LOW);

        phase.drop_objection(this);
    endtask

endclass
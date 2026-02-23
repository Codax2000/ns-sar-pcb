`timescale 1ns/1ps

/**
Class: adc_env

Environment for a differential-input ADC with SPI, plus digital system
clock and reset.
*/
class adc_env extends uvm_env;

    `uvm_component_utils (adc_env)

    // Variable: m_env_cfg
    // The environment configuration for this class. Contains virtual interfaces
    // and specific ADC environment variables.
    adc_env_cfg m_env_cfg;

    // Variable: m_spi
    // SPI agent instance
    spi_agent     m_spi;

    // Variable: m_spi_cfg
    // Configuration object built and sent to the SPI agent
    spi_agent_cfg m_spi_cfg;

    // Variable: m_clk
    // System clock agent
    oscillator_agent m_clk;

    // Variable: m_clk_cfg
    // Configuration object for the clock agent
    oscillator_agent_cfg m_clk_cfg;

    // Variable: m_adc_in
    // ADC input generator, which in this case is differential.
    sine_agent m_adc_in;

    // Variable: m_adc_in_cfg
    // Configuration object for the ADC input agent
    sine_agent_cfg m_adc_in_cfg;

    // Variable: m_reset
    // Single-bit bus agent that serves as a reset generator
    bit_bus_agent #(.WIDTH(1)) m_reset;

    // Variable: m_reset_cfg
    // Config object for <m_reset>.
    bit_bus_agent_cfg #(.WIDTH(1)) m_reset_cfg;

    // Variable: m_reg_env
    // The register environment for this ADC. Parametrized for SPI and this register block.
    reg_env #(.SEQ_ITEM(spi_packet), .ADAPTER(reg2spi_adapter), .REG_BLOCK(adc_regs)) m_reg_env;

    // Variable: m_spi_packet_splitter
    // Subscriber to SPI monitor that splits monitored packets into RAL-digestible chunks.
    spi_packet_splitter m_spi_packet_splitter;

    // Variable: m_ral
    // Utility variable. Points to the RAL instance within <m_reg_env>. Much more intuitive to
    // invoke "the RAL in the ADC env" than "the RAL in the register environment in the ADC env."
    adc_regs m_ral;

    // Variable: reset_duration
    // The duration of the initial reset pulse in seconds
    real reset_duration;

    // Variable: system_clk_frequency
    // The speed in Hz at which the system clock is running
    real system_clk_frequency;

    function new(string name = "adc_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db #(adc_env_cfg)::get(this, "", "m_env_cfg", m_env_cfg))
            `uvm_fatal(get_full_name(), "Could not attach environment config")
        
        create_configs();

        uvm_config_db #(spi_agent_cfg)::set(this, "m_spi", "cfg", m_spi_cfg);
        uvm_config_db #(oscillator_agent_cfg)::set(this, "m_clk", "cfg", m_clk_cfg);
        uvm_config_db #(bit_bus_agent_cfg #(.WIDTH(1)))::set(this, "m_reset", "cfg", m_reset_cfg);
        uvm_config_db #(sine_agent_cfg)::set(this, "m_adc_in", "cfg", m_adc_in_cfg);
        
        m_spi    = spi_agent::type_id::create("m_spi", this);
        m_clk    = oscillator_agent::type_id::create("m_clk", this);
        m_reset  = bit_bus_agent #(.WIDTH(1))::type_id::create("m_reset", this);
        m_adc_in = sine_agent::type_id::create("m_adc_in", this);

        m_reg_env = reg_env #(.SEQ_ITEM(spi_packet), .ADAPTER(reg2spi_adapter), .REG_BLOCK(adc_regs))::
                    type_id::create("m_reg_env", this);
        m_spi_packet_splitter = spi_packet_splitter::type_id::create("m_spi_packet_splitter", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        m_ral = m_reg_env.ral;
        ral.default_map.set_sequencer(spi.sequencer, m_reg_env.adapter);

        // add a packet splitter between the SPI monitor and register predictor to break up burst transactions
        spi.monitor.mon_analysis_port.connect(m_spi_packet_splitter.analysis_export);
        m_spi_packet_splitter.ap.connect(m_reg_env.predictor.bus_in);
    endfunction

    /**
    Function: reset_phase
    Resets the ADC with a disabled ADC input and with a system clock speed that was configured,
    as if the device had just powered up and the crystal had started to oscillate.

    The phase ends when the SPI agent reads back a 1 from the reset readback, indicating
    that the device has successfully been reset.
    */
    virtual task reset_phase(uvm_phase phase);
        oscillator_single_packet_seq  clk_seq;
        single_value_seq #(.WIDTH(1)) reset_seq;
        oscillator_single_packet_seq  adc_seq;
        uvm_status_e                  status;
        uvm_reg_data_t                value;

        real time_start;
        real time_reset;

        phase.raise_objection(this);
        
        clk_seq   = oscillator_single_packet_seq ::type_id::create("clk_seq");
        reset_seq = single_value_seq #(.WIDTH(1))::type_id::create("reset_seq");
        adc_seq   = oscillator_single_packet_seq ::type_id::create("adc_seq");

        clk_seq.randomize() with {
            pkt_enabled == 1;
            pkt_frequency_int == int'(this.system_clk_frequency);
        };
        reset_seq.randomize() with {
            seq_value == 1;
        };
        adc_seq.randomize() with {
            pkt_enabled == 0;
        };

        fork
            clk_seq.start(m_clk.sequencer);
            reset_seq.start(m_reset.sequencer);
            adc_seq.start(m_adc_in.sequencer);
        join

        #(reset_duration / 1e9); // delay reset duration in ns instead of seconds
        
        reset_seq.randomize() with {
            seq_value == 0;
        };
        reset_seq.start(m_reset.sequencer);

        // add a timeout with UVM_FATAL if it times out (100 * reset duration should be fine)
        time_start = $realtime();
        do begin
            m_ral.RUN_CTRL.SYNC_RESET_RB.read(status, value);
        end while (((value == 0) || (status != UVM_IS_OK)) && (($realtime() - time_start) <= (100 * (reset_duration / 1e9))));
        
        if ((value == 0) || (status != UVM_IS_OK))
            `uvm_fatal(get_full_name(), "Reset request timed out, reset did not deassert cleanly. Value is 0 or status is not OK.")

        phase.drop_objection(this);
    endtask

    /**
    Function: create_configs
    Create agent configurations. Broken out from the rest of the environment
    build phase in case child classes want to change the environment without
    having to rebuild the whole environment.

    An example might look like this; If a user wanted to enable SVA on only the SPI
    agent, then they would set the environment config checks_enable = 0 and then:

    === SystemVerilog ===
    virtual function void create_configs();
        super.create_configs();
        m_spi_cfg.checks_enable = 1; // enable SVA before the agent is actually built
    endfunction
    ===
    */
    virtual function void create_configs();
        m_spi_cfg = spi_agent_cfg::type_id::create("m_spi_cfg");
        m_spi_cfg.vif = m_env_cfg.vif_spi;
        m_spi_cfg.clk_speed_hz = m_env_cfg.spi_clk_frequency;
        m_spi_cfg.is_active = UVM_ACTIVE;
        m_spi_cfg.checks_enable = m_env_cfg.checks_enable;
        m_spi_cfg.coverage_enable = m_env_cfg.coverage_enable;

        m_clk_cfg = oscillator_agent_cfg::type_id::create("m_clk_cfg");
        m_clk_cfg.vif = m_env_cfg.vif_clk;
        m_clk_cfg.is_active = UVM_ACTIVE;
        m_clk_cfg.checks_enable = m_env_cfg.checks_enable;
        m_clk_cfg.coverage_enable = m_env_cfg.coverage_enable;
        m_clk_cfg.frequency_threshold = 0.005; // 0.5% should cause a change
        m_clk_cfg.timeout_time_ns = 1e3; // 1 MHz minimum clock speed

        m_reset_cfg = bit_bus_agent_cfg #(.WIDTH(1))::type_id::create("m_reset_cfg");
        m_reset_cfg.vif = m_env_cfg.vif_reset;
        m_reset_cfg.is_active = UVM_ACTIVE;
        m_reset_cfg.checks_enable = m_env_cfg.checks_enable;
        m_reset_cfg.coverage_enable = m_env_cfg.coverage_enable;

        m_clk_cfg = oscillator_agent_cfg::type_id::create("m_clk_cfg");
        m_clk_cfg.vif = m_env_cfg.vif_clk;
        m_clk_cfg.is_active = UVM_ACTIVE;
        m_clk_cfg.checks_enable = m_env_cfg.checks_enable;
        m_clk_cfg.coverage_enable = m_env_cfg.coverage_enable;
        m_clk_cfg.frequency_threshold = 0.005; // 0.5% should cause a change
        m_clk_cfg.timeout_time_ns = 1e6; // minimum input speed of 1 kHz, may have to change

        this.reset_duration = m_env_cfg.reset_duration;
        this.system_clk_frequency = m_env_cfg.system_clk_frequency;
    endfunction

endclass
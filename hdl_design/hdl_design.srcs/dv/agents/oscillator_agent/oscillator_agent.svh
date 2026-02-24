/**
Class: oscillator_agent

Instantiates monitor, sequencer, and driver for driving oscillator packets.
*/
class oscillator_agent extends uvm_agent;

    // Variable: m_agent_cfg
    // Agent configuration that must be set for this agent's uvm_config_db:cfg variable,
    // or the agent will throw a UVM_FATAL. Critical, since it contains the virtual interface,
    // among other things like whether this agent is active or passive.
    oscillator_agent_cfg m_agent_cfg;

    // Variable: m_coverage_collector
    // Created if the config coverage collection is enabled. Collects default coverage on the
    // packets received via this monitor.
    oscillator_coverage_collector m_coverage_collector;

    oscillator_driver driver;
    oscillator_monitor monitor;
    uvm_sequencer #(oscillator_packet) sequencer;

    `uvm_component_utils(oscillator_agent)

    function new (string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(oscillator_agent_cfg)::get(this, "", "cfg", m_agent_cfg))
            `uvm_fatal(get_full_name(), "Could not attach agent config");

        uvm_config_db #(virtual oscillator_if)::set(this, "driver", "vif", m_agent_cfg.vif);
        uvm_config_db #(virtual oscillator_if)::set(this, "monitor", "vif", m_agent_cfg.vif);
        uvm_config_db #(real)::set(this, "monitor", "frequency_threshold", m_agent_cfg.frequency_threshold);
        uvm_config_db #(real)::set(this, "monitor", "timeout_time_ns", m_agent_cfg.timeout_time_ns);
        uvm_config_db #(uvm_active_passive_enum)::set(this, "", "is_active", m_agent_cfg.is_active);

        monitor = oscillator_monitor::type_id::create("monitor", this);
        if (m_agent_cfg.is_active) begin
            driver = oscillator_driver::type_id::create("driver", this);
            sequencer = uvm_sequencer #(oscillator_packet)::type_id::create("sequencer", this);
        end
        if (m_agent_cfg.coverage_enable)
            m_coverage_collector = oscillator_coverage_collector::type_id::create("m_coverage_collector", this);

    endfunction

    virtual function void connect_phase (uvm_phase phase);
        if (m_agent_cfg.is_active)
            driver.seq_item_port.connect(sequencer.seq_item_export);
        if (m_agent_cfg.coverage_enable)
            monitor.mon_analysis_port.connect(m_coverage_collector.analysis_export);
    endfunction

endclass
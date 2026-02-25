/**
Class: sine_agent

Provides configuration for driver and monitor, and also adds coverage collection
for mixed-signal sine waves instead of just normal ones.
*/
class sine_agent extends oscillator_agent;

    `uvm_component_utils(sine_agent)

    function new (string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    sine_coverage_collector m_sine_coverage_collector;

    sine_agent_cfg m_sine_agent_cfg;

    virtual function void build_phase(uvm_phase phase);

        if (!uvm_config_db #(oscillator_agent_cfg)::get(this, "", "cfg", m_agent_cfg))
            `uvm_fatal(get_full_name(), "Could not attach agent config");

        // if configured agent config is not a sine config, retrieve individual values
        if (! $cast(m_sine_agent_cfg, m_agent_cfg)) begin
            m_sine_agent_cfg = sine_agent_cfg::type_id::create("m_sine_agent_cfg");

            if (! uvm_config_db #(sine_proxy)::get(this, "", "vproxy", m_sine_agent_cfg.vproxy))
                `uvm_fatal(get_full_name(), "Could not attach agent config or direct sine proxy")
            if (m_agent_cfg.is_active && 
                (! uvm_config_db #(int)::get(this, "", "points_per_period", m_sine_agent_cfg.points_per_period)))
                `uvm_fatal(get_full_name(), "Could not attach active agent config or direct driver points per period")
            if (! uvm_config_db #(real)::get(this, "", "amplitude_threshold", m_sine_agent_cfg.amplitude_threshold))
                `uvm_fatal(get_full_name(), "Could not attach agent config or direct amplitude threshold")
        end

        uvm_config_db #(sine_proxy)::set(this, "driver", "vproxy", m_sine_agent_cfg.vproxy);
        uvm_config_db #(sine_proxy)::set(this, "monitor", "vproxy", m_sine_agent_cfg.vproxy);
        uvm_config_db #(int)::set(this, "driver", "points_per_period", m_sine_agent_cfg.points_per_period);
        uvm_config_db #(real)::set(this, "monitor", "amplitude_threshold", m_sine_agent_cfg.amplitude_threshold);

        oscillator_driver::type_id::set_inst_override(
            sine_driver::get_type(), 
            "driver",
            this
        );
        oscillator_monitor::type_id::set_inst_override(
            sine_monitor::get_type(), 
            "monitor",
            this
        );
        oscillator_packet::type_id::set_inst_override(
            sine_packet::get_type(), 
            "sequencer.pkt",
            this
        );

        super.build_phase(phase);
    endfunction

endclass
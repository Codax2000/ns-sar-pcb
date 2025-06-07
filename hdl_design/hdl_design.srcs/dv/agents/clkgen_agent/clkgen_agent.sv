class clkgen_agent extends uvm_agent;

    `uvm_component_utils(clkgen_agent)

    // agent components
    clkgen_driver driver;
    clkgen_monitor monitor;
    uvm_sequencer #(clkgen_packet) sequencer;

    clkgen_agent_cfg cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(clkgen_agent_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("CLKGEN_AGENT", "Could not attach agent config")
        uvm_config_db #(virtual if_clkgen)::set(this, "driver", "vif", cfg.vif);
        uvm_config_db #(int)::set(this, "sequencer", "sys_clk", cfg.sys_clk);
        uvm_config_db #(virtual if_clkgen)::set(this, "monitor", "vif", cfg.vif);
        
        monitor = clkgen_monitor::type_id::create("monitor", this);
        if (get_is_active()) begin
            driver = clkgen_driver::type_id::create("driver", this);
            sequencer = uvm_sequencer #(clkgen_packet)::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        if (get_is_active())
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
class clkgen_agent extends uvm_agent;

    `uvm_component_utils(clkgen_agent)

    // agent components
    clkgen_driver driver;
    clkgen_monitor monitor;
    clkgen_sequencer sequencer;

    virtual if_clkgen vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(virtual if_clkgen)::get(this, "", "vif", vif))
            `uvm_fatal("CLKGEN_AGENT", "Could not find virtual interface")
        uvm_config_db #(virtual if_clkgen)::set(this, "driver", "vif", vif);
        uvm_config_db #(virtual if_clkgen)::set(this, "monitor", "vif", vif);
        
        monitor = clkgen_monitor::type_id::create("monitor", this);
        if (get_is_active()) begin
            driver = clkgen_driver::type_id::create("driver", this);
            sequencer = clkgen_sequencer::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        if (get_is_active())
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
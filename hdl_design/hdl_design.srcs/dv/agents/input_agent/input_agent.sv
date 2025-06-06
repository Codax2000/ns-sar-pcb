class input_agent extends uvm_agent;

    `uvm_component_utils(input_agent)

    // agent components
    input_driver driver;
    input_monitor monitor;
    uvm_sequencer #(sin_packet) sequencer;

    input_agent_cfg cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(input_agent_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("INPUT_AGENT", "Could not find config");

        uvm_config_db #(virtual if_input)::set(this, "driver", "vif", cfg.vif);
        uvm_config_db #(virtual if_input)::set(this, "monitor", "vif", cfg.vif);
        uvm_config_db #(uvm_active_passive_enum)::set(this, "", "is_active", cfg.is_active);
        
        // set sampling time and NFFT
        uvm_config_db #(int) :: set(this, "driver", "fs", cfg.fs);
        uvm_config_db #(int) :: set(this, "driver", "nfft", cfg.nffg);

        monitor = input_monitor::type_id::create("monitor", this);
        if (get_is_active()) begin
            driver = input_driver::type_id::create("driver", this);
            sequencer = input_sequencer::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        if (get_is_active())
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
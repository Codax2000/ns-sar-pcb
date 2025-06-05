class input_agent extends uvm_agent;

    `uvm_component_utils(input_agent)

    // agent components
    input_driver driver;
    input_monitor monitor;
    input_sequencer sequencer;

    virtual if_input vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(virtual if_input)::get(this, "", "vif", vif))
            `uvm_fatal("INPUT_AGENT", "Could not find virtual interface");
        uvm_config_db #(virtual if_input)::set(this, "driver", "vif", vif);
        uvm_config_db #(virtual if_input)::set(this, "monitor", "vif", vif);

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
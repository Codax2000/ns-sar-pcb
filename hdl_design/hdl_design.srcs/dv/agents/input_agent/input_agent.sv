class input_agent extends uvm_agent;

    `uvm_component_utils(input_agent)

    // agent components
    input_driver driver;
    input_monitor monitor;
    input_sequencer sequencer;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        monitor = input_monitor::type_id::create("monitor", this);
        if (get_is_active()) begin
            driver = input_driver::type_id::create("driver", this);
            sequencer = input_driver::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phas);
        if (get_is_active())
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
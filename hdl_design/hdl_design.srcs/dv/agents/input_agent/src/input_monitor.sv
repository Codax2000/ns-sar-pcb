class input_monitor extends uvm_monitor;
    `uvm_component_utils(input_monitor)

    virtual input_interface vif;
    uvm_analysis_port #(sin_packet) mon_analysis_port;

    // data collection variables

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual input_interface)::get(this, "", "vif_input", vif)) begin
            `uvm_fatal("MON", "Virtual interface not found!")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        forever begin
            sin_packet item = new();
            collect_transaction(item);
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(sin_packet item);
        @(vif.amplitude or vif.frequency);
        item.amplitude = vif.amplitude;
        item.frequency = vif.frequency;
    endtask

endclass
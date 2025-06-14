class input_monitor extends uvm_monitor;
    `uvm_component_utils(input_monitor)

    virtual if_input vif;
    uvm_analysis_port #(sin_packet) mon_analysis_port;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_input)::get(this, "", "vif", vif)) begin
            `uvm_fatal("MON", "Virtual interface not found for input monitor")
        end
    endfunction

    virtual task run_phase(uvm_phase phase);
        sin_packet item;
        forever begin
            item = new();
            collect_transaction(item);
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(sin_packet item);
        @(posedge vif.values_changed);
        item.amplitude = vif.amplitude;
        item.frequency = vif.frequency;
    endtask

endclass
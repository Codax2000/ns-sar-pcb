class clkgen_monitor extends uvm_monitor;

    `uvm_component_utils(clkgen_monitor)

    virtual if_clkgen vif;
    uvm_analysis_port #(clkgen_packet) mon_analysis_port;

    // data collection variables
    int clk_period_in_ns;
    int clk_frequency_in_khz;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_analysis_port = new("mon_analysis_port", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db#(virtual if_clkgen)::get(this, "", "vif", vif))
            `uvm_fatal("MON", "Virtual interface not found for CLKGEN Monitor")
    endfunction

    virtual task run_phase(uvm_phase phase);
        forever begin
            clkgen_packet item = new();
            collect_transaction(item);
            mon_analysis_port.write(item);
        end
    endtask

    virtual task collect_transaction(clkgen_packet item);
        @(negedge vif.rst_b);
        `uvm_info("CLKGEN_MONITOR", "Collecting clock gen packet", UVM_MEDIUM)
    endtask

endclass
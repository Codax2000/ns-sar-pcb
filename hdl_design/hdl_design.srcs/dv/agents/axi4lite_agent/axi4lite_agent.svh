class axi4lite_agent extends uvm_agent;
    `uvm_component_utils(axi4lite_agent)

    axi4lite_config                  cfg;
    uvm_sequencer #(axi4lite_packet) sequencer;
    axi4lite_driver                  driver;
    axi4lite_monitor                 monitor;
    axi4lite_coverage                coverage;

    function new(string name = "axi4lite_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(axi4lite_config)::get(this, "", "axi4lite_cfg", cfg)) begin
            `uvm_fatal("NOCFG", "Agent failed to retrieve config object")
        end

        // Always instantiate passive elements
        monitor  = axi4lite_monitor::type_id::create("monitor", this);
        coverage = axi4lite_coverage::type_id::create("coverage", this);
        coverage.enable = cfg.coverage_enable;

        // Conditionally instantiate active components
        if (cfg.is_active == UVM_ACTIVE) begin
            sequencer = uvm_sequencer#(axi4lite_packet)::type_id::create("sequencer", this);
            driver    = axi4lite_driver::type_id::create("driver", this);
        end
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Connect monitor to functional coverage group
        monitor.ap.connect(coverage.analysis_export);

        // Active connection path
        if (cfg.is_active == UVM_ACTIVE) begin
            driver.seq_packet_port.connect(sequencer.seq_packet_export);
        end
    endfunction
endclass
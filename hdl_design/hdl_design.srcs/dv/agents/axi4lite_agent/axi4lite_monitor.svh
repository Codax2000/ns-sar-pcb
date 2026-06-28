class axi4_lite_monitor extends uvm_monitor;
    `uvm_component_utils(axi4_lite_monitor)

    virtual axi4_lite_if vif;
    axi4lite_config    cfg;
    uvm_analysis_port #(axi4lite_packet) ap;

    function new(string name = "axi4_lite_monitor", uvm_component parent = null);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(axi4lite_config)::get(this, "", "axi4lite_cfg", cfg)) begin
        `uvm_fatal("NOCFG", "Config object not found in config_db")
        end
        vif = cfg.vif;
    endfunction

    virtual task run_phase(uvm_phase phase);
        forever begin
            @(posedge vif.ACLK);
            if (vif.RESETn) begin
                fork
                    sample_write();
                    sample_read();
                join_any
                disable fork;
            end
        end
    </task>

    task sample_write();
        if (vif.AWVALID && vif.AWREADY) begin
            axi4lite_packet item = axi4lite_packet::type_id::create("mon_write_item");
            item.op_type = AXI_WRITE;
            item.addr    = vif.AWADDR;
            
            while (!(vif.WVALID && vif.WREADY))
                @(posedge vif.ACLK);
            item.wdata   = vif.WDATA;
            item.wstrb   = vif.WSTRB;
            
            while (!(vif.BVALID && vif.BREADY))
                @(posedge vif.ACLK);
            item.resp    = vif.BRESP;

            ap.write(item);
        end
    endtask

    task sample_read();
        if (vif.ARVALID && vif.ARREADY) begin
            axi4lite_packet item = axi4lite_packet::type_id::create("mon_read_item");
            item.op_type = AXI_READ;
            item.addr    = vif.ARADDR;
            
            while (!(vif.RVALID && vif.RREADY))
                @(posedge vif.ACLK);
            item.rdata   = vif.RDATA;
            item.resp    = vif.RRESP;
            ap.write(item);
        end
    endtask
endclass
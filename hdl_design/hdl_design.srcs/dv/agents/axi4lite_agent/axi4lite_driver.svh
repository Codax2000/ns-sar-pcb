class axi4lite_driver extends uvm_driver #(axi4lite_packet);
  `uvm_component_utils(axi4lite_driver)

  virtual axi4_lite_if vif;
  axi4_lite_config    cfg;

  function new(string name = "axi4lite_driver", uvm_component parent = null);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(axi4_lite_config)::get(this, "", "axi4_lite_cfg", cfg)) begin
      `uvm_fatal("NOCFG", "Config object not found in config_db")
    end
    vif = cfg.vif;
  endfunction

  virtual task run_phase(uvm_phase phase);
    // Reset driving lines
    vif.AWVALID <= 0; vif.WVALID  <= 0; vif.BREADY  <= 0;
    vif.ARVALID <= 0; vif.RREADY  <= 0;
    
    @(posedge vif.ACLK);
    
    forever begin
      seq_item_port.get_next_item(req);
      if (req.op_type == AXI_WRITE) execute_write(req);
      else                          execute_read(req);
      seq_item_port.item_done();
    end
  endtask

  task execute_write(axi4lite_packet item);
    vif.AWADDR  <= item.addr;
    vif.AWVALID <= 1;
    vif.WDATA   <= item.wdata;
    vif.WSTRB   <= item.wstrb;
    vif.WVALID  <= 1;
    vif.BREADY  <= 1;

    fork
      begin : aw_hs
        while (!vif.AWREADY) @(posedge vif.ACLK);
        vif.AWVALID <= 0;
      end
      begin : w_hs
        while (!vif.WREADY) @(posedge vif.ACLK);
        vif.WVALID <= 0;
      end
    join

    while (!vif.BVALID) @(posedge vif.ACLK);
    item.resp = vif.BRESP;
    vif.BREADY <= 0;
  endtask

  task execute_read(axi4lite_packet item);
    vif.ARADDR  <= item.addr;
    vif.ARVALID <= 1;
    vif.RREADY  <= 1;

    while (!vif.ARREADY) @(posedge vif.ACLK);
    vif.ARVALID <= 0;

    while (!vif.RVALID) @(posedge vif.ACLK);
    item.rdata = vif.RDATA;
    item.resp  = vif.RRESP;
    vif.RREADY <= 0;
  endtask
endclass
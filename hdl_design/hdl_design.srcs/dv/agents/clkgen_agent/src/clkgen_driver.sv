class clkgen_driver extends uvm_driver #(clkgen_packet);

    `uvm_component_utils(clkgen_driver)

    clkgen_packet req;

    virtual if_clkgen vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual if_clkgen)::get(this, "", "vif", vif))
            `uvm_fatal("DRV", "No interface found for the CLKGEN driver")
    endfunction

    virtual task run_phase(uvm_phase phase);
        vif.clk = 1'b0;
        vif.rst_b = 1'b1;
        forever begin
            seq_item_port.get_next_item(req);
            drive_signals(req);
            seq_item_port.item_done();
        end
    endtask

    virtual task drive_signals(clkgen_packet req);
        vif.clk_period_in_ns = req.clk_period_ns;
        vif.reset_duration_in_ns = req.rst_period_ns;
        vif.reset_delay_in_ns = req.rst_delay_ns;
        
        vif.run_clk_and_reset();

        // drive the clock, but wait for the reset to be deasserted and then the clock to have a positive edge before reporting done
        wait(vif.rst_b == 1'b1);
        wait(vif.clk == 1'b1);
        wait(vif.clk == 1'b0);
    endtask

endclass
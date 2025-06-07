class start_clk_seq extends uvm_sequence #(clkgen_packet);

    `uvm_object_utils(start_clk_seq)
    `uvm_declare_p_sequencer(uvm_sequencer #(clkgen_packet))

    int sys_clk;

    function new (string name = "start_clk_seq");
        super.new(name);
    endfunction

    virtual task body();
        clkgen_packet pkt;

        `uvm_info("CLKGEN_SEQ", "Starting CLKGEN sequence", UVM_MEDIUM)
        if (!uvm_config_db #(int)::get(p_sequencer, "", "sys_clk", sys_clk))
            `uvm_fatal("CLKGEN_SEQ", "Could not attach sequence system clock")
        pkt = clkgen_packet::type_id::create("pkt");
        pkt.set_clk_period(1e9 / sys_clk);
        pkt.randomize();
        pkt.print();

        start_item(pkt);
        finish_item(pkt);
        `uvm_info("CLKGEN_SEQ", "Finished CLKGEN sequence", UVM_MEDIUM)
    endtask

endclass
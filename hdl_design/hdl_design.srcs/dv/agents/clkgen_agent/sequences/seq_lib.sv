class start_clk_seq extends uvm_sequence #(clkgen_packet);

    `uvm_object_utils(start_clk_seq)

    function new (string name = "start_clk_seq");
        super.new(name);
    endfunction

    virtual task body();
        clkgen_packet pkt;
        pkt = clkgen_packet::type_id::create("pkt");

        start_item(pkt);
        pkt.randomize();
        finish_item(pkt);
    endtask

endclass
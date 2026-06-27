class axi4lite_coverage extends uvm_subscriber #(axi4lite_packet);
    `uvm_component_utils(axi4lite_coverage)

    axi4lite_packet pkt;
    bit             enable;

    covergroup axi4_lite_cg;
        // Ensure both Reads and Writes occur
        cp_op_type: coverpoint pkt.op_type iff (enable);

        // Track targets: SPI Adapter area vs. DAC area
        cp_addr: coverpoint pkt.addr iff (enable) {
            bins spi_space = {[32'h0000_0000 : 32'h0000_00FF]};
            bins dac_space = {[32'h0000_8100 : 32'h0000_81FF]};
            illegal_bins unmapped = default;
        }
    endgroup

    function new(string name = "axi4lite_coverage", uvm_component parent = null);
        super.new(name, parent);
        axi4_lite_cg = new();
    endfunction

    virtual function void write(axi4lite_packet t);
        this.pkt = t;
        axi4_lite_cg.sample();
    endfunction
endclass
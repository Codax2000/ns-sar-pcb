class clkgen_packet extends uvm_sequence_item;

    rand integer clk_period_ns;
    rand integer rst_period_ns;
    rand integer rst_delay_ns;

    // constrain to 1-100MHz
    constraint valid_clk_frequency {
        clk_period_ns >= 10;
        clk_period_ns <= 1000;
    }
    constraint valid_reset {
        rst_period_ns <= 10 * clk_period_ns;
        rst_period_ns >= 2  * clk_period_ns;
        rst_delay_ns  <= 2  * clk_period_ns;
        rst_delay_ns  >= 0;
    }

    `uvm_object_utils_begin(clkgen_packet)
        `uvm_field_int(clk_period_ns, UVM_ALL_ON)
        `uvm_field_int(rst_period_ns, UVM_ALL_ON)
        `uvm_field_int(rst_delay_ns, UVM_ALL_ON)
    `uvm_object_utils_end

    function new (string name = "clkgen_packet");
        super.new(name);
        `uvm_info("PKT", "CLKGEN packet created", "UVM_LOW")
    endfunction

endclass
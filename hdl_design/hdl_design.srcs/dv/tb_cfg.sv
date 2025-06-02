module tb_cfg extends uvm_object ();

    `uvm_object_utils(tb_cfg)

    rand int nfft_power;
    rand int osr_power;
    rand int clk_div;
    rand bit is_dwa;

         int clk_div;
         int nfft;

    virtual if_spi vif_spi;
    virtual if_clkgen vif_clkgen;
    virtual if_input vif_input;
    virtual if_status vif_status;

    constraint legal_osr {
        osr_power <= 7;
        osr_power >= 1;
    }

    constraint legal_nfft {
        nfft_power < 16;
        nfft_power > 0;
    }

    constraint legal_clk_div {
        clk_div >= 0;
        clk_div < 16;
    }

    function post_randomize();
        nfft = 1 << nfft_power;
        clk_div = 1 << clk_div_power;
    endfunction

    function print();
        `uvm_info("TB_CFG", $sformat("Randomized Config:\n%s", this.sprint()), UVM_MEDIUM)
    endfunction

endmodule
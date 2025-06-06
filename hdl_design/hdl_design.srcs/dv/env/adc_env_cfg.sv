import uvm_pkg::*;
`include "uvm_macros.svh"

class adc_env_cfg extends uvm_object;

    `uvm_object_utils(adc_env_cfg)

    // agent virtual interfaces
    virtual if_spi vif_spi;
    virtual if_clkgen vif_clkgen;
    virtual if_input vif_input;

    // randomized register/clock fields
    rand int sys_clk;
    rand int nfft_power;
    rand int osr_power;
    rand int clk_div;
    rand bit is_dwa;
    
    // post-randomization fields
    int osr;
    int nfft;

    // simulation coverage fields
    bit checks_enable;
    bit coverage_enable;

    // constraints literally match HW/RTL constraints
    constraint system_clk_matches_syn {
        sys_clk == 100e6;
    }

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

    function void post_randomize();
        nfft = 1 << nfft_power;
        osr = 1 << osr_power;
    endfunction

    function new(name = "adc_env_cfg");
        super.new(name);
    endfunction
endclass
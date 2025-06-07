import uvm_pkg::*;
`include "uvm_macros.svh"

class adc_env_cfg extends uvm_object;

    `uvm_object_utils_begin(adc_env_cfg)
        `uvm_field_real(vdd, UVM_DEFAULT)
        `uvm_field_int(sys_clk, UVM_DEFAULT)
        `uvm_field_int(nfft, UVM_DEFAULT)
        `uvm_field_int(osr, UVM_DEFAULT)
        `uvm_field_int(is_dwa, UVM_DEFAULT)
        `uvm_field_int(clk_div, UVM_DEFAULT)
    `uvm_object_utils_end

    // agent virtual interfaces
    virtual if_spi vif_spi;
    virtual if_clkgen vif_clkgen;
    virtual if_input vif_input;

    // board parameters
    rand int  vdd_index;
         real vdd_options [3];
         real vdd;
    rand int  sys_clk;
    rand int  spi_clk;

    // randomized register fields
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
    constraint clk_matches_syn {
        sys_clk == 100000000;
        spi_clk ==   2000000;
    }

    constraint legal_vdd {
        vdd_index <  3;
        vdd_index >= 0;
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
        vdd = vdd_options[vdd_index];
    endfunction

    function new(name = "adc_env_cfg");
        super.new(name);
        vdd_options[0] = 1.8;
        vdd_options[1] = 2.5;
        vdd_options[2] = 3.3;
    endfunction
endclass
import uvm_pkg::*;
`include "uvm_macros.svh"

class adc_env_cfg extends uvm_object;

    `uvm_object_utils_begin(adc_env_cfg)
        `uvm_field_real(vdd, UVM_DEFAULT)
        `uvm_field_int(sys_clk, UVM_DEFAULT)
        `uvm_field_int(spi_clk, UVM_DEFAULT)
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

    // TODO: randomized register fields
    rand int nfft_power;
    rand int osr_power;
    rand int clk_div;

    // TODO: post-randomization fields
    int osr;
    int nfft;

    // simulation coverage fields
    bit checks_enable;
    bit coverage_enable;

    // constraints literally match HW/RTL constraints
    constraint clk_matches_syn {
        sys_clk ==  24000000; // 24 MHz crystal oscillator
        spi_clk ==   2000000; // 2 MHz SPI clock
    }

    constraint legal_vdd {
        vdd_index <  3;
        vdd_index >= 0;
    }

    function void post_randomize();
        vdd = vdd_options[vdd_index];
        osr = 1 << osr_power;
        nfft = 1 << nfft_power;
    endfunction

    function new(name = "adc_env_cfg");
        super.new(name);
        vdd_options[0] = 1.8;
        vdd_options[1] = 2.5;
        vdd_options[2] = 3.3;
    endfunction
endclass
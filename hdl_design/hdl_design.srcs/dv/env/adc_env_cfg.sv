import uvm_pkg::*;
`include "uvm_macros.svh"

class adc_env_cfg extends uvm_object;

    `uvm_object_utils_begin(adc_env_cfg)
        `uvm_field_real(vdd, UVM_DEFAULT)
        `uvm_field_int(sys_clk, UVM_DEFAULT)
        `uvm_field_int(spi_clk, UVM_DEFAULT)
        `uvm_field_int(nfft_power, UVM_DEFAULT)
        `uvm_field_int(osr_power, UVM_DEFAULT)
        `uvm_field_int(dwa_en, UVM_DEFAULT)
        `uvm_field_int(n_sh_total_cycles, UVM_DEFAULT)
        `uvm_field_int(n_sh_active_cycles, UVM_DEFAULT)
        `uvm_field_int(n_bottom_plate_active_cycles, UVM_DEFAULT)
        `uvm_field_int(n_sar_cycles, UVM_DEFAULT)
        `uvm_field_int(n_int1_total_cycles, UVM_DEFAULT)
        `uvm_field_int(n_int1_active_cycles, UVM_DEFAULT)
        `uvm_field_int(n_int2_total_cycles, UVM_DEFAULT)
        `uvm_field_int(n_int2_active_cycles, UVM_DEFAULT)
        `uvm_field_int(checks_enable, UVM_DEFAULT)
        `uvm_field_int(coverage_enable, UVM_DEFAULT)
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
    rand bit dwa_en;

    // timing information
    rand int n_sh_total_cycles;
    rand int n_sh_active_cycles;
    rand int n_bottom_plate_active_cycles;
    rand int n_sar_cycles;
    rand int n_int1_total_cycles;
    rand int n_int1_active_cycles;
    rand int n_int2_total_cycles;
    rand int n_int2_active_cycles;

    // post-randomization fields
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
        vdd_index inside {[1:3]};
    }

    constraint legal_osr_power {
        osr_power inside {[0:((2**8)-1)]};
    }

    constraint legal_nfft_power {
        nfft_power inside {[0:((2**14)-1)]};
    }

    constraint active_lte_total {
        n_sh_total_cycles            inside {[1:((2**16)-1)]};
        n_sh_active_cycles           inside {[1:((2**16)-1)]};
        n_bottom_plate_active_cycles inside {[1:((2**16)-1)]};
        n_sar_cycles                 inside {[1:((2**16)-1)]};
        n_int1_total_cycles          inside {[1:((2**16)-1)]};
        n_int1_active_cycles         inside {[1:((2**16)-1)]};
        n_int2_total_cycles          inside {[1:((2**16)-1)]};
        n_int2_active_cycles         inside {[1:((2**16)-1)]};

        n_sh_active_cycles <= n_sh_total_cycles;
        n_bottom_plate_active_cycles <= n_sh_active_cycles;
        n_int1_active_cycles <= n_int1_total_cycles;
        n_int2_active_cycles <= n_int2_total_cycles;
    }

    function void post_randomize();
        osr = 1 << osr_power;
        nfft = 1 << nfft_power;
        vdd = vdd_options[vdd_index];
    endfunction

    function new(name = "adc_env_cfg");
        super.new(name);
        vdd_options = {1.8, 2.5, 3.3};
    endfunction
endclass
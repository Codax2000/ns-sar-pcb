class ral_nfft_power extends uvm_reg;

    rand uvm_reg_field nfft_power;
    
    `uvm_object_utils(ral_nfft_power)

    function new (string name = "ral_nfft_power");
        super.new(name, 4, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.nfft_power = uvm_reg_field::type_id::create("nfft_power", , get_full_name());
        this.nfft_power.configure(
            this, 4, 0, "RW", 0, 4'h8, 1, 0, 1
        );
    endfunction

endclass

// TODO: Define other register classes

class ral_registers extends uvm_reg_block;
    rand ral_nfft_power nfft_pow;

    `uvm_object_utils(ral_registers)

    function new(string name = "ral_registers");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function build();
        this.default_map = create_map(/* TODO: Finish map */);

        // add all registers
        this.nfft_pow = ral_nfft_power::type_id::create("nfft_pow", , get_full_name());
        this.nfft_pow.configure(this, null, "");
        this.nfft_pow.build();
        this.default_map.add_reg(this.nfft_pow, `UVM_REG_ADDR_WIDTH'h0, "RW", 0);
    endfunction
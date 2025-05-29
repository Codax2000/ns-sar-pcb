class ral_nfft_power extends uvm_reg;

    rand uvm_reg_field nfft_power;

    `uvm_object_utils(ral_nfft_power)

    function new (string name = "ral_nfft_power");
        super.new(name, 4, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.nfft_power = uvm_reg_field::type_id::create("nfft_power", , get_full_name());
        this.nfft_power.configure(
            this, 4, 0, "RW", 0, 4'h8, 1, 1, 1
        );
    endfunction

endclass

class ral_osr_dwa extends uvm_reg;

    rand uvm_reg_field osr;
    rand uvm_reg_field dwa_enable;

    `uvm_object_utils(ral_osr_dwa)

    function new (string name = "ral_osr_dwa");
        super.new(name, 4, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.osr = uvm_reg_field::type_id::create("osr", , get_full_name());
        this.dwa_enable = uvm_reg_field::type_id::create("dwa_enable", , get_full_name());

        this.osr.configure(
            this, 3, 1, "RW", 0, 3'h2, 1, 1, 0
        );
        this.dwa_enable.configure(
            this, 1, 0, "RW", 0, 1'h0, 1, 1, 0
        );
    endfunction

endclass

class ral_sample_clk_div extends uvm_reg;

    rand uvm_reg_field sample_clk_div;

    `uvm_object_utils(ral_sample_clk_div)

    function new (string name = "ral_sample_clk_div");
        super.new(name, 4, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.sample_clk_div = uvm_reg_field::type_id::create("sample_clk_div", , get_full_name());
        this.sample_clk_div.configure(
            this, 4, 0, "RW", 0, 4'h0, 1, 1, 0
        );
    endfunction

endclass

class ral_status extends uvm_reg;

    uvm_reg_field begin_sample;
    uvm_reg_field read_mem;
    uvm_reg_field fsm_status;

    `uvm_object_utils(ral_status)

    function new (string name = "ral_status");
        super.new(name, 4, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.begin_sample = uvm_reg_field::type_id::create("begin_sample", , get_full_name());
        this.read_mem = uvm_reg_field::type_id::create("read_mem", , get_full_name());
        this.fsm_status = uvm_reg_field::type_id::create("fsm_status", , get_full_name());

        this.begin_sample.configure(
            this, 1, 3, "W1C", 0, 0, 0, 0, 0
        );
        this.read_mem.configure(
            this, 1, 2, "W1C", 0, 0, 0, 0, 0
        );
        this.fsm_status.configure(
            this, 2, 0, "RO", 0, 2'b00, 1, 0, 0
        );
    endfunction

endclass

class ral_registers extends uvm_reg_block;

    rand ral_nfft_power nfft_pow;
    rand ral_osr_dwa osr_dwa;
    rand ral_sample_clk_div sample_clk_div;
         ral_status status;

    `uvm_object_utils(ral_registers)

    function new(string name = "ral_registers");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function build();
        this.default_map = create_map("default_map", 0, 1, UVM_LITTLE_ENDIAN);

        // add all registers
        this.nfft_pow = ral_nfft_power::type_id::create("nfft_pow", , get_full_name());
        this.nfft_pow.configure(this, null, "");
        this.nfft_pow.build();
        this.default_map.add_reg(this.nfft_pow, `UVM_REG_ADDR_WIDTH'h0, "RW");

        this.osr_dwa = osr_dwa::type_id::create("osr_dwa", , get_full_name());
        this.osr_dwa.configure(this, null, "");
        this.osr_dwa.build();
        this.default_map.add_reg(this.osr_dwa, `UVM_REG_ADDR_WIDTH'h1, "RW");

        this.sample_clk_div = sample_clk_div::type_id::create("sample_clk_div", , get_full_name());
        this.sample_clk_div.configure(this, null, "");
        this.sample_clk_div.build();
        this.default_map.add_reg(this.sample_clk_div, `UVM_REG_ADDR_WIDTH'h2, "RW");

        this.status = status::type_id::create("status", , get_full_name());
        this.status.configure(this, null, "");
        this.status.build();
        this.default_map.add_reg(this.status, `UVM_REG_ADDR_WIDTH'h3, "RW");

    endfunction

endclass
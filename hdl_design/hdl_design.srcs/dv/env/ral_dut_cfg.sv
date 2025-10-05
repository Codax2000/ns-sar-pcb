import uvm_pkg::*;
`include "uvm_macros.svh"

class ral_register_0 extends uvm_reg;
    uvm_reg_field NFFT_POWER;
    uvm_reg_field DWA_EN;

    `uvm_object_utils(ral_register_0)

    function new (string name = "ral_register_0");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.NFFT_POWER = uvm_reg_field::type_id::create("NFFT_POWER", , get_full_name());
        this.NFFT_POWER.configure(
            this,
            14,
            0,
            "RW",
            0,
            0,
            1,
            0,
            0
        );
        this.DWA_EN = uvm_reg_field::type_id::create("DWA_EN", , get_full_name());
        this.DWA_EN.configure(
            this,
            1,
            15,
            "RW",
            0,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_1 extends uvm_reg;
    uvm_reg_field OSR_POWER;

    `uvm_object_utils(ral_register_1)

    function new (string name = "ral_register_1");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.OSR_POWER = uvm_reg_field::type_id::create("OSR_POWER", , get_full_name());
        this.OSR_POWER.configure(
            this,
            8,
            0,
            "RW",
            0,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_2 extends uvm_reg;
    uvm_reg_field N_SH_TOTAL_CYCLES;

    `uvm_object_utils(ral_register_2)

    function new (string name = "ral_register_2");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_SH_TOTAL_CYCLES = uvm_reg_field::type_id::create("N_SH_TOTAL_CYCLES", , get_full_name());
        this.N_SH_TOTAL_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_3 extends uvm_reg;
    uvm_reg_field N_SH_ACTIVE_CYCLES;

    `uvm_object_utils(ral_register_3)

    function new (string name = "ral_register_3");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_SH_ACTIVE_CYCLES = uvm_reg_field::type_id::create("N_SH_ACTIVE_CYCLES", , get_full_name());
        this.N_SH_ACTIVE_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_4 extends uvm_reg;
    uvm_reg_field N_BOTTOM_PLATE_ACTIVE_CYCLES;

    `uvm_object_utils(ral_register_4)

    function new (string name = "ral_register_4");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_BOTTOM_PLATE_ACTIVE_CYCLES = uvm_reg_field::type_id::create("N_BOTTOM_PLATE_ACTIVE_CYCLES", , get_full_name());
        this.N_BOTTOM_PLATE_ACTIVE_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_5 extends uvm_reg;
    uvm_reg_field N_SAR_CYCLES;

    `uvm_object_utils(ral_register_5)

    function new (string name = "ral_register_5");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_SAR_CYCLES = uvm_reg_field::type_id::create("N_SAR_CYCLES", , get_full_name());
        this.N_SAR_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_6 extends uvm_reg;
    uvm_reg_field N_INT1_TOTAL_CYCLES;

    `uvm_object_utils(ral_register_6)

    function new (string name = "ral_register_6");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_INT1_TOTAL_CYCLES = uvm_reg_field::type_id::create("N_INT1_TOTAL_CYCLES", , get_full_name());
        this.N_INT1_TOTAL_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_7 extends uvm_reg;
    uvm_reg_field N_INT1_ACTIVE_CYCLES;

    `uvm_object_utils(ral_register_7)

    function new (string name = "ral_register_7");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_INT1_ACTIVE_CYCLES = uvm_reg_field::type_id::create("N_INT1_ACTIVE_CYCLES", , get_full_name());
        this.N_INT1_ACTIVE_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_8 extends uvm_reg;
    uvm_reg_field N_INT2_TOTAL_CYCLES;

    `uvm_object_utils(ral_register_8)

    function new (string name = "ral_register_8");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_INT2_TOTAL_CYCLES = uvm_reg_field::type_id::create("N_INT2_TOTAL_CYCLES", , get_full_name());
        this.N_INT2_TOTAL_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_9 extends uvm_reg;
    uvm_reg_field N_INT2_ACTIVE_CYCLES;

    `uvm_object_utils(ral_register_9)

    function new (string name = "ral_register_9");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.N_INT2_ACTIVE_CYCLES = uvm_reg_field::type_id::create("N_INT2_ACTIVE_CYCLES", , get_full_name());
        this.N_INT2_ACTIVE_CYCLES.configure(
            this,
            16,
            0,
            "RW",
            0,
            1,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_10 extends uvm_reg;
    uvm_reg_field START_CONVERSION;
    uvm_reg_field MAIN_STATE_RB;

    `uvm_object_utils(ral_register_10)

    function new (string name = "ral_register_10");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.START_CONVERSION = uvm_reg_field::type_id::create("START_CONVERSION", , get_full_name());
        this.START_CONVERSION.configure(
            this,
            1,
            0,
            "W1S",
            1,
            0,
            1,
            0,
            0
        );
        this.MAIN_STATE_RB = uvm_reg_field::type_id::create("MAIN_STATE_RB", , get_full_name());
        this.MAIN_STATE_RB.configure(
            this,
            3,
            1,
            "RO",
            1,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_11 extends uvm_reg;
    uvm_reg_field CLKGEN_DRP_DADDR;

    `uvm_object_utils(ral_register_11)

    function new (string name = "ral_register_11");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.CLKGEN_DRP_DADDR = uvm_reg_field::type_id::create("CLKGEN_DRP_DADDR", , get_full_name());
        this.CLKGEN_DRP_DADDR.configure(
            this,
            7,
            0,
            "RW",
            0,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_12 extends uvm_reg;
    uvm_reg_field CLKGEN_DRP_DI;

    `uvm_object_utils(ral_register_12)

    function new (string name = "ral_register_12");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.CLKGEN_DRP_DI = uvm_reg_field::type_id::create("CLKGEN_DRP_DI", , get_full_name());
        this.CLKGEN_DRP_DI.configure(
            this,
            16,
            0,
            "RW",
            0,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_13 extends uvm_reg;
    uvm_reg_field CLKGEN_DRP_DO;

    `uvm_object_utils(ral_register_13)

    function new (string name = "ral_register_13");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.CLKGEN_DRP_DO = uvm_reg_field::type_id::create("CLKGEN_DRP_DO", , get_full_name());
        this.CLKGEN_DRP_DO.configure(
            this,
            16,
            0,
            "RO",
            0,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class ral_register_14 extends uvm_reg;
    uvm_reg_field CLKGEN_DRP_RD_EN;
    uvm_reg_field CLKGEN_DRP_WR_EN;

    `uvm_object_utils(ral_register_14)

    function new (string name = "ral_register_14");
        super.new(name,16,build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function void build();
        this.CLKGEN_DRP_RD_EN = uvm_reg_field::type_id::create("CLKGEN_DRP_RD_EN", , get_full_name());
        this.CLKGEN_DRP_RD_EN.configure(
            this,
            1,
            0,
            "W1S",
            1,
            0,
            1,
            0,
            0
        );
        this.CLKGEN_DRP_WR_EN = uvm_reg_field::type_id::create("CLKGEN_DRP_WR_EN", , get_full_name());
        this.CLKGEN_DRP_WR_EN.configure(
            this,
            1,
            1,
            "W1S",
            1,
            0,
            1,
            0,
            0
        );
    endfunction

endclass

class dut_memory extends uvm_reg_block;
    ral_register_0 register_0;
    ral_register_1 register_1;
    ral_register_2 register_2;
    ral_register_3 register_3;
    ral_register_4 register_4;
    ral_register_5 register_5;
    ral_register_6 register_6;
    ral_register_7 register_7;
    ral_register_8 register_8;
    ral_register_9 register_9;
    ral_register_10 register_10;
    ral_register_11 register_11;
    ral_register_12 register_12;
    ral_register_13 register_13;
    ral_register_14 register_14;
    uvm_mem adc_mem;

    `uvm_object_utils(dut_memory)

    function new (string name = "dut_memory");
        super.new(name, build_coverage(UVM_NO_COVERAGE));
    endfunction

    virtual function build();
        this.default_map = create_map("default_map", 0, 2, UVM_LITTLE_ENDIAN);

        this.register_0 = ral_register_0::type_id::create("register_0", , get_full_name());
        this.register_0.configure(this, null, "");
        this.register_0.build();
        this.default_map.add_reg(this.register_0, `UVM_REG_ADDR_WIDTH'h0, "RW");

        this.register_1 = ral_register_1::type_id::create("register_1", , get_full_name());
        this.register_1.configure(this, null, "");
        this.register_1.build();
        this.default_map.add_reg(this.register_1, `UVM_REG_ADDR_WIDTH'h1, "RW");

        this.register_2 = ral_register_2::type_id::create("register_2", , get_full_name());
        this.register_2.configure(this, null, "");
        this.register_2.build();
        this.default_map.add_reg(this.register_2, `UVM_REG_ADDR_WIDTH'h2, "RW");

        this.register_3 = ral_register_3::type_id::create("register_3", , get_full_name());
        this.register_3.configure(this, null, "");
        this.register_3.build();
        this.default_map.add_reg(this.register_3, `UVM_REG_ADDR_WIDTH'h3, "RW");

        this.register_4 = ral_register_4::type_id::create("register_4", , get_full_name());
        this.register_4.configure(this, null, "");
        this.register_4.build();
        this.default_map.add_reg(this.register_4, `UVM_REG_ADDR_WIDTH'h4, "RW");

        this.register_5 = ral_register_5::type_id::create("register_5", , get_full_name());
        this.register_5.configure(this, null, "");
        this.register_5.build();
        this.default_map.add_reg(this.register_5, `UVM_REG_ADDR_WIDTH'h5, "RW");

        this.register_6 = ral_register_6::type_id::create("register_6", , get_full_name());
        this.register_6.configure(this, null, "");
        this.register_6.build();
        this.default_map.add_reg(this.register_6, `UVM_REG_ADDR_WIDTH'h6, "RW");

        this.register_7 = ral_register_7::type_id::create("register_7", , get_full_name());
        this.register_7.configure(this, null, "");
        this.register_7.build();
        this.default_map.add_reg(this.register_7, `UVM_REG_ADDR_WIDTH'h7, "RW");

        this.register_8 = ral_register_8::type_id::create("register_8", , get_full_name());
        this.register_8.configure(this, null, "");
        this.register_8.build();
        this.default_map.add_reg(this.register_8, `UVM_REG_ADDR_WIDTH'h8, "RW");

        this.register_9 = ral_register_9::type_id::create("register_9", , get_full_name());
        this.register_9.configure(this, null, "");
        this.register_9.build();
        this.default_map.add_reg(this.register_9, `UVM_REG_ADDR_WIDTH'h9, "RW");

        this.register_10 = ral_register_10::type_id::create("register_10", , get_full_name());
        this.register_10.configure(this, null, "");
        this.register_10.build();
        this.default_map.add_reg(this.register_10, `UVM_REG_ADDR_WIDTH'h10, "RW");

        this.register_11 = ral_register_11::type_id::create("register_11", , get_full_name());
        this.register_11.configure(this, null, "");
        this.register_11.build();
        this.default_map.add_reg(this.register_11, `UVM_REG_ADDR_WIDTH'h11, "RW");

        this.register_12 = ral_register_12::type_id::create("register_12", , get_full_name());
        this.register_12.configure(this, null, "");
        this.register_12.build();
        this.default_map.add_reg(this.register_12, `UVM_REG_ADDR_WIDTH'h12, "RW");

        this.register_13 = ral_register_13::type_id::create("register_13", , get_full_name());
        this.register_13.configure(this, null, "");
        this.register_13.build();
        this.default_map.add_reg(this.register_13, `UVM_REG_ADDR_WIDTH'h13, "RW");

        this.register_14 = ral_register_14::type_id::create("register_14", , get_full_name());
        this.register_14.configure(this, null, "");
        this.register_14.build();
        this.default_map.add_reg(this.register_14, `UVM_REG_ADDR_WIDTH'h14, "RW");

        this.adc_mem = new("adc_mem", 16384, 16, "RO");
        this.adc_mem.configure(this);
        this.default_map.add_mem(this.adc_mem, 16384, "RO");
    endfunction
endclass

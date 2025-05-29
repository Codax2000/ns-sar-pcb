class reg_env extends uvm_env;

    `uvm_component_utils(reg_env)
    function new (string name = "reg_env", uvm_component parent);
        super.new(name, parent);
    endfunction

    uvm_agent                       agent;
    ral_cfg                         ral_model;
    reg2spi_adapter                 adapter;
    uvm_reg_predictor #(spi_packet) spi_predictor;

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ral_model = ral_cfg::type_id::create("ral_model", this);
        adapter = adapter::type_id::create("adapter");
        predictor = uvm_reg_predictor #(spi_packet)::type_id::create("spi_predictor", this);

        ral_model.build();
        ral_model.lock_model();
        uvm_config_db #(ral_cfg)::set(null, "uvm_test_top", "ral_model", ral_model);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        spi_predictor.map = ral_model.default_map;
        spi_predictor.adapter = adapter;
        agent.ap.connect(spi_predictor.bus_in);
    endfunction

endclass
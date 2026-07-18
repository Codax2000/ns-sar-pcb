/**
Class: spi_env

Generic SPI + RAL environment, with register splitter that goes between SPI
and the RAL to handle burst transactions.

Transactions are dealt with as such:
SPI Monitor -> SPI packet splitter -> SPI reg subscriber -> UVM Adapter -> RAL
*/
class spi_env extends uvm_env;

    `uvm_component_utils(spi_env)

    reg2spi_adapter                 m_adapter;
    spi_agent                       m_spi_agent;
    spi_packet_splitter             m_packet_splitter;
    spi_reg_subscriber              m_interposer;
    uvm_reg_predictor #(spi_packet) m_predictor;
    uvm_reg_block                   regmodel;

    function new(string name = "spi_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction : new

    virtual function void build_phase(uvm_phase phase);
        spi_env_cfg cfg;

        super.build_phase(phase);

        // Get config object
        if (!uvm_config_db #(spi_env_cfg)::get(this, "", "cfg", cfg)) begin
            `uvm_fatal(get_full_name(), "Could not get spi_env_cfg from config_db");
        end

        if (!cfg.has_external_ral()) begin
            `uvm_fatal(
                get_full_name(),
                "No RAL specified in config"
            )
        end
        else begin
            `uvm_info(
                get_full_name(),
                $sformatf(
                    "External RAL is supplied in spi_env_cfg; %0s will use a pointer to that instance.",
                    get_full_name()
                ),
                UVM_LOW
            );
            regmodel = cfg.regmodel;
        end
        uvm_config_db #(uvm_reg_block)::set(this, "m_interposer", "m_ral", regmodel);

        // Set spi_agent_cfg into config_db for spi_agent
        uvm_config_db #(spi_agent_cfg)::set(this, "m_spi_agent", "cfg", cfg.m_spi_agent_cfg);
        m_spi_agent = spi_agent::type_id::create("m_spi_agent", this);
        m_packet_splitter = spi_packet_splitter::type_id::create("m_packet_splitter", this);
        m_interposer = spi_reg_subscriber::type_id::create("m_interposer", this);
        m_predictor = uvm_reg_predictor #(spi_packet)::type_id::create("m_predictor", this);    
        m_adapter = reg2spi_adapter::type_id::create("adapter");
        
    endfunction : build_phase

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // connect register chain
        m_spi_agent.monitor.mon_analysis_port.connect(m_packet_splitter.analysis_export);
        m_packet_splitter.ap.connect(m_interposer.analysis_export);
        m_interposer.reg_analysis_port.connect(m_predictor.bus_in);
        m_predictor.map = regmodel.default_map;
        m_predictor.adapter = m_adapter;
    endfunction : connect_phase

endclass : spi_env

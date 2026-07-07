/**
Class: spi_env

Generic SPI + RAL environment, with register splitter that goes between SPI
and the RAL to handle burst transactions.

Transactions are dealt with as such:
SPI Monitor -> SPI packet splitter -> SPI reg subscriber -> UVM Adapter -> RAL
*/
class spi_env #(
    type REG_BLOCK      = uvm_reg_block,
    type SPI_SUBSCRIBER = spi_reg_subscriber #(REG_BLOCK)
) extends uvm_env;

    `uvm_component_param_utils(spi_env#(REG_BLOCK, SPI_SUBSCRIBER))

    spi_env_cfg #(REG_BLOCK) m_cfg;

    // Variable: m_ral
    // Effective register block for this environment, whether supplied by the
    // parent or built locally inside m_reg_env.
    REG_BLOCK m_ral;

    spi_agent m_spi_agent;

    reg_env #(
        .SEQ_ITEM (spi_packet),
        .ADAPTER  (reg2spi_adapter),
        .REG_BLOCK(REG_BLOCK)
    ) m_reg_env;

    SPI_SUBSCRIBER m_interposer;

    spi_packet_splitter m_packet_splitter;

    function new(string name = "spi_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction : new

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Get config object
        if (!uvm_config_db #(spi_env_cfg #(REG_BLOCK))::get(this, "", "cfg", m_cfg)) begin
            `uvm_fatal(get_full_name(), "Could not get spi_env_cfg from config_db");
        end
        
        if (m_cfg.m_reg_env_cfg == null) begin
            `uvm_info(
                get_full_name(),
                "No reg_env_cfg in spi_env_cfg; creating default (standalone RAL).",
                UVM_LOW
            );
            m_cfg.m_reg_env_cfg = reg_env_cfg #(REG_BLOCK)::type_id::create("m_reg_env_cfg");
        end

        if (!m_cfg.has_external_ral()) begin
            `uvm_info(
                get_full_name(),
                $sformatf(
                    "No external RAL supplied in spi_env_cfg; %0s will build a standalone %0s block.",
                    get_full_name(),
                    REG_BLOCK::get_type_name()
                ),
                UVM_LOW
            );
        end

        // Set spi_agent_cfg into config_db for spi_agent
        uvm_config_db #(spi_agent_cfg)::set(this, "m_spi_agent", "cfg", m_cfg.m_spi_agent_cfg);

        m_spi_agent = spi_agent::type_id::create("m_spi_agent", this);

        uvm_config_db #(reg_env_cfg #(REG_BLOCK))::set(
            this, "m_reg_env", "cfg", m_cfg.m_reg_env_cfg
        );
        m_reg_env = reg_env#(spi_packet, reg2spi_adapter, REG_BLOCK)::type_id::create("m_reg_env", this);

        m_interposer = SPI_SUBSCRIBER::type_id::create("m_interposer", this);
        m_packet_splitter = spi_packet_splitter::type_id::create("m_packet_splitter", this);
    endfunction : build_phase

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        m_ral = m_reg_env.ral;
        m_interposer.m_ral = m_ral;

        if (m_cfg.has_external_ral() && m_cfg.m_reg_env_cfg.m_ral != m_ral) begin
            `uvm_error(
                get_full_name(),
                "External RAL handle in reg_env_cfg does not match reg_env.ral after build."
            );
        end

        // Connect SPI Monitor to SPI packet splitter
        m_spi_agent.monitor.mon_analysis_port.connect(m_packet_splitter.analysis_export);

        // Connect packet splitter's output to the SPI reg subscriber (interposer)
        m_packet_splitter.ap.connect(m_interposer.analysis_export);

        // Connect the interposer's analysis port to the reg predictor's bus_in
        m_interposer.reg_analysis_port.connect(m_reg_env.predictor.bus_in);
    end function : connect_phase

endclass : spi_env

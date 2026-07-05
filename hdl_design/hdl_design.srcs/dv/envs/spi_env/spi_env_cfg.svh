/**
Class: spi_env_cfg

Configuration object for the SPI environment. Contains the SPI agent
configuration and a reg_env_cfg that is forwarded to the internal reg_env
via config_db before reg_env is created.
*/
class spi_env_cfg #(
    type REG_BLOCK = uvm_reg_block
) extends uvm_object;

    `uvm_object_param_utils(spi_env_cfg#(REG_BLOCK))

    // Variable: m_spi_agent_cfg
    // Configuration object for the internal SPI agent.
    spi_agent_cfg m_spi_agent_cfg;

    // Variable: m_reg_env_cfg
    // Register environment configuration, forwarded to reg_env via config_db.
    reg_env_cfg #(REG_BLOCK) m_reg_env_cfg;

    function new(string name = "spi_env_cfg");
        super.new(name);
    endfunction : new

    // Function: has_external_ral
    // Returns 1 when a parent (e.g. base_test) supplied the register block.
    function bit has_external_ral();
        return (m_reg_env_cfg != null) && m_reg_env_cfg.has_external_ral();
    endfunction : has_external_ral

endclass : spi_env_cfg

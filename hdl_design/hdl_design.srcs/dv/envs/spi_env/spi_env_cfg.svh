/**
Class: spi_env_cfg

Configuration object for the SPI environment. Contains virtual interfaces,
checks and coverage enable flags, the SPI agent configuration, and the
RAL sub-block for this specific SPI interface.
*/
class spi_env_cfg #(
    type REG_BLOCK = uvm_reg_block
) extends uvm_object;

    `uvm_object_param_utils(spi_env_cfg#(REG_BLOCK))

    // Variable: m_spi_agent_cfg
    // Configuration object for the internal SPI agent.
    spi_agent_cfg m_spi_agent_cfg;

    // Variable: m_ral
    // The RAL sub-block that this SPI environment will interact with.
    REG_BLOCK m_ral;

    function new(string name = "spi_env_cfg");
        super.new(name);
    endfunction : new

endclass : spi_env_cfg

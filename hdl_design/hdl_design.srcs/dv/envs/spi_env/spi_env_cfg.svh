/**
Class: spi_env_cfg

Configuration object for the SPI environment. Contains the SPI agent
configuration and a reg_env_cfg that is forwarded to the internal reg_env
via config_db before reg_env is created.
*/
class spi_env_cfg extends uvm_object;

    `uvm_object_utils(spi_env_cfg)

    // Variable: m_spi_agent_cfg
    // Configuration object for the internal SPI agent.
    spi_agent_cfg m_spi_agent_cfg;

    // Variable: regmodel
    // Register block instance.
    uvm_reg_block regmodel;

    function new(string name = "spi_env_cfg");
        super.new(name);
    endfunction : new

    // Function: has_external_ral
    // Returns 1 when a parent (e.g. base_test) supplied the register block.
    function bit has_external_ral();
        return (regmodel != null);
    endfunction : has_external_ral

endclass : spi_env_cfg

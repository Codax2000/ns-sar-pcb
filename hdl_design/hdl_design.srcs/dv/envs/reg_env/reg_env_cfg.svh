/**
Class: reg_env_cfg

Configuration object for reg_env. Carries an optional pre-built register
sub-block; when m_ral is null, reg_env builds a standalone REG_BLOCK of
the parametrized type during build_phase.
*/
class reg_env_cfg #(
    type REG_BLOCK = uvm_reg_block
) extends uvm_object;

    `uvm_object_param_utils(reg_env_cfg#(REG_BLOCK))

    // Variable: m_ral
    // Optional register block supplied by a parent (e.g. base_test chip_top).
    REG_BLOCK m_ral;

    function new(string name = "reg_env_cfg");
        super.new(name);
    endfunction : new

    // Function: has_external_ral
    // Returns 1 when a parent supplied the register block.
    function bit has_external_ral();
        return (m_ral != null);
    endfunction : has_external_ral

endclass : reg_env_cfg

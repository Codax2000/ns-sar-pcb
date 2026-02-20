/**
Class: bit_bus_agent_cfg

Contains virtual interface and configuration variables for the bit bus agent.
*/
class bit_bus_agent_cfg #(int WIDTH = 1) extends uvm_object;

    `uvm_object_param_utils(bit_bus_agent_cfg #(WIDTH))

    function new(string name = "bit_bus_agent_cfg");
        super.new(name);
    endfunction

    // Virtual interface for this agent
    virtual if_bit_bus #(WIDTH) vif;

    // Agent activity
    uvm_active_passive_enum is_active;

    // Optional knobs for consistency with other agents
    rand bit checks_enable;
    rand bit coverage_enable;

endclass
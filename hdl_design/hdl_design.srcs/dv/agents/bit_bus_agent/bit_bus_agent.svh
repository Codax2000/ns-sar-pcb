/**
 * Class: bit_bus_agent
 *
 * Generic N‑bit agent with driver, monitor, and sequencer.
 * Uses <bit_bus_agent_cfg> for configuration.
 */
class bit_bus_agent #(int WIDTH = 1) extends uvm_agent;

    `uvm_component_param_utils(bit_bus_agent #(WIDTH))

    bit_bus_driver  #(WIDTH) driver;
    bit_bus_monitor #(WIDTH) monitor;
    uvm_sequencer   #(bit_bus_packet #(WIDTH)) sequencer;

    bit_bus_agent_cfg #(WIDTH) cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(bit_bus_agent_cfg #(WIDTH))::get(this, "", "cfg", cfg))
            `uvm_fatal("BIT_BUS_AGENT", "Could not attach bit_bus_agent_cfg")

        // Pass config fields down via config_db, following existing conventions
        uvm_config_db #(virtual bit_bus_if #(WIDTH))::set(this, "driver",  "vif", cfg.vif);
        uvm_config_db #(virtual bit_bus_if #(WIDTH))::set(this, "monitor", "vif", cfg.vif);

        monitor = bit_bus_monitor #(WIDTH)::type_id::create("monitor", this);

        if (cfg.is_active == UVM_ACTIVE) begin
            driver    = bit_bus_driver  #(WIDTH)::type_id::create("driver", this);
            sequencer = uvm_sequencer   #(bit_bus_packet #(WIDTH))::type_id::create("sequencer", this);
        end
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (cfg.is_active == UVM_ACTIVE)
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
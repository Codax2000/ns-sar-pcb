class spi_test extends uvm_test;

    `uvm_component_utils(spi_test)

    function new(string name = "spi_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    spi_agent agent;
    spi_packet_wrapper seq;

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);
        uvm_config_db#(uvm_active_passive_enum)::set(this, "agent", "is_active", UVM_ACTIVE);
        uvm_config_db#(int)::set(null, "", "nfft", 16);
        agent = spi_agent::type_id::create("agent", this);
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
    endfunction

    virtual task run_phase(uvm_phase phase);
        phase.raise_objection(this);
        seq = spi_packet_wrapper::type_id::create("seq");
        `uvm_info("TEST", "Sequence initialized", UVM_LOW)
        seq.start(agent.sequencer);
        phase.drop_objection(this);
    endtask

endclass
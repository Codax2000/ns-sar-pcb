class base_test extends uvm_test;

    `uvm_component_utils (base_test)

    function new(string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    input_agent agent;

    virtual function void build_phase (uvm_phase phase);
        super.build_phase(phase);
        agent = input_agent::type_id::create("agent", this);
        agent.is_active = UVM_ACTIVE;
        uvm_config_db#(int)::set(this, "", "nfft", 512);
        uvm_config_db#(int)::set(this, "", "driver_delay_ns", 512);
    endfunction

    virtual function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
    endfunction

    virtual task run_phase(uvm_phase phase);
        phase.raise_objection(this);
        drive_sin_wave seq = drive_sine_wave::type_id::create("seq");
        seq.start(agent.sequencer);
        phase.drop_objection(this);
    endtask

endclass

class random_value_test extends base_test;

    virtual task run_phase(uvm_phase phase);
        phase.raise_objection(this);
        drive_random_values seq = drive_random_values::type_id::create("seq");
        seq.start(agent.sequencer);
        phase.drop_objection(this);
    endtask

endclass
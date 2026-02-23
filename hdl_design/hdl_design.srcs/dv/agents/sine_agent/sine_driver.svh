/**
Class: sine_driver

Oscillator agent capable of driving sine waves.
*/
class sine_driver extends oscillator_driver;

    `uvm_component_utils(sine_driver)

    sine_proxy vproxy;

    sine_packet ms_req;

    int points_per_period;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (! uvm_config_db #(sine_proxy)::get(this, "", "vproxy", vproxy))
            `uvm_fatal(get_full_name(), "Could not find driver proxy")
        if (! uvm_config_db #(int)::get(this, "", "points_per_period", points_per_period))
            `uvm_fatal(get_full_name(), "Could not find driver points per period")
        super.build_phase(phase);
    endfunction

    virtual task run_phase(uvm_phase phase);
        vproxy.configure_driver(points_per_period);
        super.run_phase(phase);
    endtask

    virtual task drive_signals(oscillator_packet req);

        super.drive_signals(req);

        if ($cast(ms_req, req))
            vproxy.push(ms_req.amplitude);

    endtask

endclass
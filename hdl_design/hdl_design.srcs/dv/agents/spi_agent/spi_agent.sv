class spi_agent extends uvm_agent;

    `uvm_component_utils(spi_agent)

    // agent components
    spi_driver driver;
    spi_monitor monitor;
    spi_sequencer sequencer;

    virtual if_spi vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(virtual if_spi)::get(this, "", "vif", vif))
            `uvm_fatal("SPI_AGENT", "Could not find virtual interface");
        uvm_config_db #(virtual if_spi)::set(this, "driver", "vif", vif);
        uvm_config_db #(virtual if_spi)::set(this, "monitor", "vif", vif);

        monitor = spi_monitor::type_id::create("monitor", this);
        if (get_is_active()) begin
            driver = spi_driver::type_id::create("driver", this);
            sequencer = spi_sequencer::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        if (get_is_active())
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
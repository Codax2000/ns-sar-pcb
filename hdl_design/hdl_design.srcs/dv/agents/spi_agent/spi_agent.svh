/**
Class: spi_agent

Instantiates driver, monitor, sequencer. Also instantiates coverage and enables
or disables SPI SVA based on configuration.
*/
class spi_agent extends uvm_agent;

    `uvm_component_utils(spi_agent)

    spi_driver driver;
    spi_monitor monitor;
    uvm_sequencer #(spi_packet) sequencer;

    virtual if_spi vif;
    spi_agent_cfg cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(spi_agent_cfg)::get(this, "", "cfg", cfg))
            `uvm_fatal("SPI_AGENT", "Could not attach SPI config");

        uvm_config_db #(uvm_active_passive_enum)::set(this, "", "is_active", cfg.is_active);
        uvm_config_db #(virtual if_spi)::set(this, "driver", "vif", cfg.vif);
        uvm_config_db #(virtual if_spi)::set(this, "monitor", "vif", cfg.vif);
        uvm_config_db #(int)::set(this, "driver", "clk_speed_hz", cfg.clk_speed_hz);

        monitor = spi_monitor::type_id::create("monitor", this);
        if (cfg.is_active) begin
            driver = spi_driver::type_id::create("driver", this);
            sequencer = uvm_sequencer #(spi_packet)::type_id::create("sequencer", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        if (cfg.is_active)
            driver.seq_item_port.connect(sequencer.seq_item_export);
    endfunction

endclass
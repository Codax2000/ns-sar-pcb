/**
Class: spi_reg_subscriber

Interposer class that deals with prediction. The `write` method should define
how registers react to various register transactions.

By default, passes packets right through to the RAL adapter without any
modification.
*/
class spi_reg_subscriber extends uvm_subscriber #(spi_packet);

    `uvm_component_utils(spi_reg_subscriber)

    uvm_reg_block m_ral;

    uvm_analysis_port #(spi_packet) reg_analysis_port;

    function new(string name = "spi_reg_subscriber", uvm_component parent = null);
        super.new(name, parent);
        reg_analysis_port = new("reg_analysis_port", this);
    endfunction : new

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db #(uvm_reg_block)::get(this, "", "m_ral", m_ral))
            `uvm_fatal(get_full_name(), "Could not attach RAL instance");
    endfunction

    virtual function void write(spi_packet t);
        // Default action: pass-through to register predictor
        reg_analysis_port.write(t);
    endfunction : write

endclass : spi_reg_subscriber

/**
Class: spi_reg_subscriber

Interposer class that deals with prediction. The `write` method should define
how registers react to various register transactions.

By default, passes packets right through to the RAL adapter without any
modification.
*/
class spi_reg_subscriber #(
    type REG_BLOCK = uvm_reg_block
) extends uvm_subscriber #(spi_packet);

    `uvm_component_param_utils(spi_reg_subscriber#(REG_BLOCK))

    REG_BLOCK m_ral;

    uvm_analysis_port #(spi_packet) reg_analysis_port;

    function new(string name = "spi_reg_subscriber", uvm_component parent = null);
        super.new(name, parent);
        reg_analysis_port = new("reg_analysis_port", this);
    endfunction : new

    virtual function void write(spi_packet t);
        // Default action: pass-through to register predictor
        reg_analysis_port.write(t);
    endfunction : write

endclass : spi_reg_subscriber

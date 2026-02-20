/**
 * Class: spi_packet_splitter
 *
 * A UVM subscriber that receives <spi_packet> transactions and provides
 * an analysis export that can be connected to RAL components such as
 * uvm_reg_predictor. 
 */
class spi_packet_splitter extends uvm_subscriber #(spi_packet);

    // Register the component with the UVM factory.
    `uvm_component_utils(spi_packet_splitter)

    /**
     * Variable: analysis_export
     *
     * Analysis export used to forward <spi_packet> transactions.
     * This export is compatible with RAL predictors, i.e. will correspond to a
     * single bus operation in the case of a burst transaction.
     */
    uvm_analysis_export #(spi_packet) analysis_export;

    function new(string name = "spi_packet_splitter",
                 uvm_component parent = null);
        super.new(name, parent);
        analysis_export = new("analysis_export", this);
    endfunction : new

    /**
     * Function: write
     *
     * Receives a <spi_packet> transaction from the analysis port.
     * This implementation is intentionally empty.
     *
     * Parameters:
     *   t - The spi_packet transaction.
     */
    virtual function void write(spi_packet t);
        // TODO: 
    endfunction : write

endclass : spi_packet_splitter
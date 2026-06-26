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
     * Variable: ap
     *
     * Analysis export used to forward <spi_packet> transactions.
     * This export is compatible with RAL predictors, i.e. will correspond to a
     * single bus operation in the case of a burst transaction.
     */
    uvm_analysis_port #(spi_packet) ap;

    function new(string name = "spi_packet_splitter",
                 uvm_component parent = null);
        super.new(name, parent);
        ap = new("ap", this);
    endfunction : new

    /**
     * Function: write
     *
     * Receives a <spi_packet> transaction from the analysis port.
     * Splits the incoming packet into 1-byte values so that the register
     * adapter can deal with it easily.
     *
     * Parameters:
     *   t - The spi_packet transaction.
     */
    virtual function void write(spi_packet t);
        spi_packet current;
        bit [7:0] mosi0, mosi1;
        bit [7:0] miso0, miso1;

        if (t.mosi.size() >= 4 && t.miso.size() >= 4) begin
            mosi0 = t.mosi.pop_front();
            mosi1 = t.mosi.pop_front();
            miso0 = t.miso.pop_front();
            miso1 = t.miso.pop_front();
            do begin
                current = spi_packet::type_id::create("current_pkt");
                current.mosi.push_back(mosi0);
                current.mosi.push_back(mosi1);
                current.mosi.push_back(t.mosi.pop_front());
                current.mosi.push_back(t.mosi.pop_front());
                
                current.miso.push_back(miso0);
                current.miso.push_back(miso1);
                current.miso.push_back(t.miso.pop_front());
                current.miso.push_back(t.miso.pop_front());
                ap.write(current);

                address++;
            end while (t.mosi.size() > 1);
        end
    endfunction : write

endclass : spi_packet_splitter
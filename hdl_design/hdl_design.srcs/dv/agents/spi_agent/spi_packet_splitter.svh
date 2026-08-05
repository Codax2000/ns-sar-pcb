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
        int  address;
        bit rd_en;
        spi_packet t_clone;

        if (t.mosi.size() >= 4 && t.miso.size() >= 4) begin
            // Clone original packet so we don't modify it directly in-place
            if (!$cast(t_clone, t.clone())) begin
                `uvm_fatal("spi_packet_splitter", "Failed to cast cloned packet")
            end

            mosi0 = t_clone.mosi.pop_front();
            mosi1 = t_clone.mosi.pop_front();
            miso0 = t_clone.miso.pop_front();
            miso1 = t_clone.miso.pop_front();

            rd_en = mosi0[7];
            address[14:0] = {mosi0[6:0], mosi1};

            while (t_clone.mosi.size() >= 2 && t_clone.miso.size() >= 2) begin
                current = spi_packet::type_id::create("current_pkt");
                
                // Form the header byte for the single transaction
                current.mosi.push_back({rd_en, address[14:8]});
                current.mosi.push_back(address[7:0]);
                
                // Dummy/empty miso headers
                current.miso.push_back(miso0);
                current.miso.push_back(miso1);

                // Add 16-bit register payload
                current.mosi.push_back(t_clone.mosi.pop_front());
                current.mosi.push_back(t_clone.mosi.pop_front());
                
                current.miso.push_back(t_clone.miso.pop_front());
                current.miso.push_back(t_clone.miso.pop_front());
                
                ap.write(current);

                address++; // Increment word address for subsequent transaction in the burst
            end
        end
    endfunction : write

endclass : spi_packet_splitter
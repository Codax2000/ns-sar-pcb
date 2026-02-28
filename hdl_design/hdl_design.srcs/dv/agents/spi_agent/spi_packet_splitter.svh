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
        bit        is_subsequent_transaction = 0;
        bit [14:0] address;

        address = t.address;
        
        // if the incoming packet is read, copy the address and leave write data
        // alone. Set the is_subsequent_transaction flag to 1 after the first one.
        do begin
            current = spi_packet::type_id::create("current_pkt");
            current.rd_en = t.rd_en;
            current.address = address;
            current.header_parity = t.header_parity;
            current.address_parity[0] = t.address_parity[0];
            current.address_parity[1] = t.address_parity[1];
            if (t.rd_en) begin
                current.n_reads = 1;
                current.read_data.push_back(t.read_data.pop_front());
                current.read_parity.push_back(t.read_parity.pop_front());
            end else begin
                current.n_reads = 0;
                current.write_data.push_back(t.write_data.pop_front());
                current.write_parity.push_back(t.write_parity.pop_front());
            end
            current.is_subsequent_transaction = is_subsequent_transaction;
            ap.write(current);

            address++;
            is_subsequent_transaction = 1;
        end while ((t.rd_en && (t.read_data.size() > 0)) || ((!t.rd_en) && (t.write_data.size() > 0)));
    endfunction : write

endclass : spi_packet_splitter
/**
 * Class: bit_bus_driver
 *
 * Drives an N‑bit value onto the DUT using <bit_bus_if>.
 */
class bit_bus_driver #(int WIDTH = 1)
    extends uvm_driver #(bit_bus_packet #(WIDTH));

    `uvm_component_param_utils(bit_bus_driver #(WIDTH))

    virtual bit_bus_if #(WIDTH) vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual bit_bus_if #(WIDTH))::get(this, "", "vif", vif))
            `uvm_fatal("BIT_BUS_DRV", "Could not attach virtual interface")
    endfunction

    virtual task run_phase(uvm_phase phase);
        bit_bus_packet #(WIDTH) req;

        forever begin
            seq_item_port.get_next_item(req);
            drive_value(req);
            seq_item_port.item_done(req);
        end
    endtask

    virtual task drive_value(bit_bus_packet req);
        `uvm_info(get_full_name(),
                  $sformatf("Driving bus value 0x%0h", req.value),
                  UVM_MEDIUM)
        vif.bit_driven = req.value;
    endtask

endclass
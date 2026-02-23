/**
 * Class: bit_bus_monitor
 *
 * Observes the DUT's N‑bit output and publishes <bit_bus_packet> items.
 */
class bit_bus_monitor #(int WIDTH = 1) extends uvm_monitor;

    `uvm_component_param_utils(bit_bus_monitor #(WIDTH))

    virtual bit_bus_if #(WIDTH) vif;
    uvm_analysis_port #(bit_bus_packet #(WIDTH)) mon_ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
        mon_ap = new("mon_ap", this);
    endfunction

    virtual function void build_phase(uvm_phase phase);
        if (!uvm_config_db #(virtual bit_bus_if #(WIDTH))::get(this, "", "vif", vif))
            `uvm_fatal("BIT_BUS_MON", "Could not attach virtual interface")
    endfunction

    virtual task run_phase(uvm_phase phase);
        bit_bus_packet #(WIDTH) pkt;

        forever begin
            @(vif.bit_observed);
            pkt = bit_bus_packet #(WIDTH)::type_id::create("mon_pkt");
            pkt.value = vif.bit_observed;

            `uvm_info("BIT_BUS_MON",
                      $sformatf("Observed bus value 0x%0h", pkt.value),
                      UVM_HIGH)

            mon_ap.write(pkt);
        end
    endtask

endclass
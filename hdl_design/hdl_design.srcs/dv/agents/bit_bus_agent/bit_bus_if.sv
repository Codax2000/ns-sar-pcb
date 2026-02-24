/**
 * Interface: bit_bus_if
 *
 * Generic N‑bit interface used for both driver and monitor.
 * Follows the same convention as other MS interfaces in the repo:
 *   - *_driven   : value driven by the UVM driver
 *   - *_observed : value observed from the DUT
 */
interface bit_bus_if #(int WIDTH = 1);

    logic [WIDTH-1:0] bit_driven;
    logic [WIDTH-1:0] bit_observed;

endinterface
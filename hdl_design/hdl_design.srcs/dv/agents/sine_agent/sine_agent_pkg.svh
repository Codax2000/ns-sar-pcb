/**
Package: sine_agent_pkg

Contains all the *classes* necessary for using the sine agent package, which
is built using UVM-MS. Users should first have UVM installed and UVM-MS as well.
The <osc_agent_pkg> should also be compiled, since it is imported here.

Contains classes:

    - <sine_packet>: a generic sine-wave extension of <osc_packet>
    - <max_amp_packet>: a sine packet constrained to use full amplitude
    - <sine_proxy>: the virtual proxy class that is used by the agents and
                    implemented in the bridge
    - <sine_agent_cfg>: the config object with additional necessary values
    - <sine_driver>: an extension of <osc_driver> that also configures sine waves
    - <sine_monitor>: an extension of <osc_monitor> that also monitors sine waves
    - <sine_coverage_collector>: like <osc_coverage_collector>, but also monitors amplitude
    - <sine_agent>: places type overrides and instantiates everything

It also includes the following modules, which can be used as standalone, without
using the mixed-signal agents.

    - <sine_ms_bridge_core> : SystemVerilog real only. Could be replaced by VerilogAMS if
                              needed, but that would be a pain in the neck. Stick with
                              this if at all possible, especially since Vivado doesn't support
                              VerilogAMS and it's unlikely that co-sim will be an option anyway.
                              If it is, most simulators should have a way to configure a real to
                              a voltage anyway.
    - <sine_ms_bridge> : bridge that implements the proxy and connects it to the bridge core.
*/
package sine_agent_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    import uvm_ms_pkg::*;
    `include "uvm_ms.svh"

    `include "sine_packet.svh"
    `include "max_amp_packet.svh"
    `include "sine_proxy.svh"
    `include "sine_agent_cfg.svh"
    `include "sine_driver.svh"
    `include "sine_monitor.svh"
    `include "sine_coverage_collector.svh"
    `include "sine_agent.svh"

endpackage
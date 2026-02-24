// ==================================================
// Proxy class to be extended in the MS Bridge module
// It allows UVM components to access proxy API 
// by passing a handle to the proxy instance via
// uvm_config_db. Class is declared virtual so it 
// cannot be instantiated, it must be derived.
// It is possible to derive from uvm_component if UVM
// phase information required in the MS bridge scope
// ==================================================

// =======================================================================
// Template Proxy class for uvm_ms that should be extended for specific
//   use case
// =======================================================================
`ifndef UVM_MS_PKG_SV
`define UVM_MS_PKG_SV
 
`include "uvm_macros.svh"
 
package uvm_ms_pkg;
  import uvm_pkg::*;
 
  /* uvm_ms_proxy provides a communication API between UVC driver/monitor and the bridge. A
   * proxy specific to the bridge should be created inside the bridge by extending
   * uvm_ms_proxy and implementing the API functions accordingly
   */

  virtual class uvm_ms_proxy;
    string name;

    function new (string name = "uvm_ms_proxy"); 
      this.name = name;
    endfunction
    // Example prototype for push function to core
    // This function should be added to a derived class
    // and NOT to the uvm_ms_proxy class
    // virtual function void push(input real ampl, bias, freq, enable);
    //  `uvm_warning("proxy","Function push not implemented")
    //endfunction
  endclass : uvm_ms_proxy

endpackage : uvm_ms_pkg
 
`endif

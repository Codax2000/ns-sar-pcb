// =======================================================================
// Wrapper function to hook the Analog Resource digital calls to the UVM 
// reporting system. Upwards name referencing  is used so it works in 
// various abstractions of the bridge core, e.g. Verilog-AMS, SystemVerilog. 
//
// The UVM messaging macros are based on class hierarchy. UVM-MS uses different
// macro names to distinguish them from the UVM macros.
//
// =======================================================================

// `uvm_ms_info works the same as `uvm_info except that it passes `__FILE__ and 
// `__LINE__ arguments pass to the info message, reporting where the macro is called,
// typically the bridge core
//
// Output format: 
// UVM_INFO <file path>(<line number>) @ <time>: reporter <tag> <message>
// ("reporter" is the typical default UVM report handler name

`define uvm_ms_info(id,message,uvm_verbosity) \
          uvm_ms_info(id,message,uvm_verbosity,`__FILE__ ,`__LINE__ );

`define uvm_ms_warning(id,message) uvm_ms_warning(id,message,`__FILE__ ,`__LINE__ );

`define uvm_ms_error(id,message) uvm_ms_error(id,message,`__FILE__ ,`__LINE__ );

`define uvm_ms_fatal(id,message) uvm_ms_fatal(id,message,`__FILE__ ,`__LINE__ );

// The uvm_ms_info function takes arguments from the `uvm_ms_info macro and recreates 
// a message identical to `uvm_info. This is needed because `uvm_ms_info is being 
// called from a module representing the bridge core and not from a UVM component.

function void uvm_ms_info(string id, string message, int verbosity_level, string file, int line);
  uvm_report_info(id,message,verbosity_level,file,line);
endfunction: uvm_ms_info

// The uvm_ms_warning function takes arguments from the `uvm_ms_warning macro and recreates 
// a message identical to `uvm_warning. This is needed because `uvm_ms_warning is being 
// called from a module representing the bridge core and not from a UVM component.

function void uvm_ms_warning(string id, string message, string file, int line);
  uvm_report_warning(id,message,,file,line);
endfunction: uvm_ms_warning

// The uvm_ms_error function takes arguments from the `uvm_ms_error macro and recreates 
// a message identical to `uvm_error. This is needed because `uvm_ms_error is being 
// called from a module representing the bridge core and not from a UVM component.

function void uvm_ms_error(string id, string message, string file, int line);
  uvm_report_error(id,message,,file,line);
endfunction: uvm_ms_error

// The uvm_ms_fatal function takes arguments from the `uvm_ms_fatal macro and recreates 
// a message identical to `uvm_fatal. This is needed because `uvm_ms_fatal is being 
// called from a module representing the bridge core and not from a UVM component.

function void uvm_ms_fatal(string id, string message, string file, int line);
  uvm_report_fatal(id,message,,file,line);
endfunction: uvm_ms_fatal

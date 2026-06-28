class axi4lite_packet extends uvm_sequence_item;
  `uvm_object_utils(axi4lite_packet)

  // Control Fields
  rand axi_op_e          op_type;

  // Address Channels
  rand bit [31:0]        addr;

  // Data Channels
  rand bit [31:0]        wdata;
  rand bit [3:0]         wstrb;   // Byte strobes for partial writes
  
  // Response Fields (populated by the Driver/Monitor)
       bit [31:0]        rdata;
       bit [1:0]         resp;    // 2'b00 = OKAY, 2'b11 = SLVERR

  // Constraints for AXI4-Lite Alignment
  constraint c_aligned_addr {
    addr[1:0] == 2'b00; // Forces 32-bit (4-byte) alignment
  }

  constraint c_valid_wstrb {
    if (op_type == AXI_WRITE) {
      wstrb != 4'b0000; // Must write at least one byte
    } else {
      wstrb == 4'b0000;
    }
  }

  // Standard Constructor
  function new(string name = "axi4lite_packet");
    super.new(name);
  endfunction

endclass
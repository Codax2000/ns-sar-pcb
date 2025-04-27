class spi_packet extends uvm_object

    rand bit [1:0] command;
    rand bit [1:0] reg_index;
    rand bit [3:0] mosi_data;

    bit  [3:0] reg_response;
    bit [15:0] mem_response [$]; // data queue

    constraint reg_is_legal { reg_index <= 2; reg_index >= 0; }
    constraint mosi_data_legal { 
        (reg_index == 0) -> mosi_data >= 6;
        (reg_index == 1) -> ((mosi_data <= 11) && (mosi_data >= 2));
    }
    constraint order { solve reg_is_legal before mosi_data_legal; }

    `uvm_field_utils_begin(spi_packet)
        `uvm_field_int(command, UVM_DEFAULT)
        `uvm_field_int(reg_index, UVM_DEFAULT)
        `uvm_field_int(mosi_data, UVM_DEFAULT)
        `uvm_field_int(reg_response, UVM_DEFAULT)
        `uvm_field_int(mem_response, UVM_NOCOMPARE)
    `uvm_field_utils_end

    function new (string name = "spi_packet");
        super.new(name);
        `uvm_info("PKT", "SPI packet created")
    endfunction

endclass
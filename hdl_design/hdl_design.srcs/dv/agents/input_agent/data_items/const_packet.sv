class const_packet extends sin_packet;

    `uvm_object_utils(const_packet)

    function new (name = "const_packet");
        super.new(name);
    endfunction

    function void post_randomize();
        super.post_randomize();
        frequency = 0;
    endfunction

endclass
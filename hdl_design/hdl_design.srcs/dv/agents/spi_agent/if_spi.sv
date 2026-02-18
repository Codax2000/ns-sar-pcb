interface if_spi ();

    logic scl;
    logic mosi;
    logic csb;
    logic miso;

    initial begin
        scl = 1'b0;
        mosi = 1'b0;
        csb = 1'b1;
    end

endinterface
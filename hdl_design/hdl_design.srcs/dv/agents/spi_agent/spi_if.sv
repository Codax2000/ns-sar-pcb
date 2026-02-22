/**
Interface: spi_if

interface for the SPI agent. Also contains SVA if enabled.
*/
interface spi_if ();

    logic scl;
    logic mosi;
    logic csb;
    logic miso;

    initial begin
        scl = 1'b0;
        mosi = 1'b0;
        csb = 1'b1;
    end

    modport dut_input (
        input csb,
        input scl,
        input mosi,
        output miso
    );

    logic enable_sva;

endinterface
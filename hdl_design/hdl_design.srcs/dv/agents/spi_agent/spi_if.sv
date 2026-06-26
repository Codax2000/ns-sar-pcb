/**
Interface: spi_if

interface for the SPI agent. Also contains SVA if enabled.
*/
interface spi_if ();

    logic scl;
    logic mosi;
    logic csb;
    logic miso;

    modport dut_input (
        input csb,
        input scl,
        input mosi,
        output miso
    );

    logic enable_sva;
    
endinterface
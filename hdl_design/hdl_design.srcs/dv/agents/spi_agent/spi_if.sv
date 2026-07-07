/**
Interface: spi_if

interface for the SPI agent. Also contains SVA if enabled.
*/
interface spi_if (
    output logic csb,
    output logic scl,
    output logic mosi,
    input  logic miso
);

    logic drive_enable;
    logic enable_sva;

    logic mosi_int;
    logic scl_int;

    assign mosi = drive_enable ? mosi_int : 1'bz;
    assign scl  = drive_enable ? scl_int  : 1'bz;
        
endinterface
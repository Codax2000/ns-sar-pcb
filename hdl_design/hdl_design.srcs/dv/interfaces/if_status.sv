/**
Interface: status_if

Used for monitoring signals for which the test needs to wait. Should only
touch signals at the digital boundary so that it's portable from RTL to
synthesis/apr simulations.
*/
interface status_if;

    logic rst_b;
    logic spi_clk;

endinterface
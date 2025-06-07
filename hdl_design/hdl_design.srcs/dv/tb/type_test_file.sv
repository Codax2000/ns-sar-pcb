`timescale 1ns/1ps

module type_test ();

    int fs;
    int clk_div;
    realtime delay;

    initial begin
        fs = 100000000;
        clk_div = 13;
        delay = 1.0*clk_div / fs;

        $display("FS = %d, clk_div = %d, delay = %.12f", fs, clk_div, delay);
    end

endmodule
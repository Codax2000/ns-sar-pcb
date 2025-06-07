`timescale 1ns/1ns

interface if_clkgen ();

    int clk_period_in_ns;
    int reset_duration_in_ns;
    int reset_delay_in_ns;

    logic clk_is_running;

    logic clk;
    logic rst_b;

    modport module_clkgen (input clk, input rst_b);

    task run_clk;
        clk = 1'b0;
        clk_is_running = 1'b1;
        while (clk_is_running)
            #(clk_period_in_ns / 2) clk = !clk;
    endtask

    task run_reset;
        rst_b = 1'b1;
        #reset_delay_in_ns;
        rst_b = 1'b0;
        #reset_duration_in_ns;
        rst_b = 1'b1;
    endtask

    task run_clk_and_reset;
        fork
            run_clk();
            run_reset();
        join_none
    endtask

endinterface
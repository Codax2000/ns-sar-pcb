module tb_cfg ();

    rand int nfft_power;
    rand int clk_div_power;
    rand bit is_dwa;

         int clk_div;
         int nfft;

    function post_randomize();
        nfft = 1 << nfft_power;
        clk_div = 1 << clk_div_power;
    endfunction

endmodule
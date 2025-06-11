interface if_reg(
    input i_clk, 
    input i_rst_b
);

    logic i_dwa_wr_en;
    logic i_dwa;

    logic       i_osr_wr_en;
    logic [2:0] i_osr_power;

    logic       i_nfft_wr_en;
    logic [3:0] i_nfft_power;

    logic       i_clk_div_wr_en;
    logic [3:0] i_clk_div;

    logic [3:0] nfft_power;
    logic [2:0] osr_power;
    logic       dwa;
    logic [3:0] clk_div;

endinterface
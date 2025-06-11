module registers (
    if_reg i_if_reg
);

    always_ff @(posedge i_if_reg.i_clk) begin
        if (!i_if_reg.i_rst_b) begin
            i_if_reg.nfft_power <= 4'h8;
            i_if_reg.osr_power <= 4'h2;
            i_if_reg.dwa <= 1'b0;
            i_if_reg.clk_div <= 1'b0;
        end else begin
            if (i_if_reg.i_dwa_wr_en)
                i_if_reg.dwa <= i_if_reg.i_dwa;

            if (i_if_reg.i_osr_wr_en)
                i_if_reg.osr_power <= i_if_reg.i_osr_power;

            if (i_if_reg.i_nfft_wr_en)
                i_if_reg.nfft_power <= i_if_reg.i_nfft_power;

            if (i_if_reg.i_clk_div_wr_en)
                i_if_reg.clk_div <= i_if_reg.i_clk_div;

        end
    end

endmodule
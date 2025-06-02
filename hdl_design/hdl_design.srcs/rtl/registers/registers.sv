module registers (
    input logic i_arst_b,

    reg_interface if_reg
);

    logic do_dwa;
    logic [15:0] nfft;
    logic [7:0 ] osr;
    logic [3:0] sampclk_div;

    always_ff @(posedge if_reg.clk or negedge i_arst_b) begin
        if (!i_arst_b) begin
            nfft <= 256;
            osr <= 8;
            do_dwa <= 1'b0;
            sampclk_div <= 4'h0;
        end else begin
            nfft <= 1 << if_reg.nfft_power;
            osr <= 1 << if_reg.osr_power;
            do_dwa <= if_reg.do_dwa;
            sampclk_div <= if_reg.sampclk_div;
        end
    end

endmodule
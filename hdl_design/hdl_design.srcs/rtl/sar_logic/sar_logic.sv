module sar_logic (
    input logic i_arst_b,
    input logic i_clk,

    // START FIFO handshake
    output logic o_ready,
    input logic i_start,

    output logic [14:0] wr_addr,
    output logic [15:0] wr_data,
    output logic        wr_en,

    input logic       i_dwa,
    input logic [3:0] i_nfft_power,
    input logic [2:0] i_osr_power,
    input logic [3:0] i_clk_div
);

    enum logic [1:0] {
        READY =0,
        DIVIDE=1,
        SHIFT =2,
        COUNT =3
    } ps_e, ns_e;

    logic [16:0] divide_counter_r, divide_counter_n, divide_value;
    logic  [3:0] shift_register_r, shift_register_n;
    logic [16:0] nfft_counter_r, nfft_counter_n;
    logic  [8:0] osr_counter_r, osr_counter_n;

    // next state logic
    always_comb begin
        case (ps_e)
            READY  : ns_e = i_start                          ? DIVIDE : READY;
            DIVIDE : ns_e = divide_counter_n == divide_value ? SHIFT  : DIVIDE;
            SHIFT  : ns_e = shift_register == 4'b0001        ? COUNT  : DIVIDE;
            COUNT  : ns_e = (nfft_counter_r == (1 << i_nfft_power) - 1) &&
                            (osr_counter_r  == (1 << i_osr_power)  - 1) ? READY : DIVIDE;
        endcase
        // TODO: set counters
        case (ps_e)
            READY  : divide_counter_n = ;
            DIVIDE : divide_counter_n = ;
            SHIFT  : divide_counter_n = ;
            COUNT  : divide_counter_n = ;
        endcase
        case (ps_e)
            READY  : osr_counter_n = ;
            DIVIDE : osr_counter_n = ;
            SHIFT  : osr_counter_n = ;
            COUNT  : osr_counter_n = ;
        endcase
        case (ps_e)
            READY  : nfft_counter_n = ;
            DIVIDE : nfft_counter_n = ;
            SHIFT  : nfft_counter_n = ;
            COUNT  : nfft_counter_n = ;
        endcase
    end

    always_ff @(posedge i_clk) begin
        if (!i_arst_b) begin
            divide_counter_r <= 0;
            osr_counter_r    <= 0;
            nfft_counter_r   <= 0;
            ps_e             <= READY;
        end else begin
            divide_counter_r <= divide_counter_n;
            osr_counter_r    <= osr_counter_n;
            nfft_counter_r   <= nfft_counter_n;
            ps_e             <= ns_e;
        end
    end

    // TODO: SAR Logic with inputs and counters for 3 SAR bits

endmodule
module sar_state_machine #(
    parameter N_SAR_BITS=3
) (
    reg_if.RD rd,
    input logic i_sar_compare,
    input logic i_reset_pointer,
    input logic i_en_sar,
    output logic [(1 << N_SAR_BITS)-1:0] o_caps_set,
    output logic [(1 << N_SAR_BITS)-1:0] o_cap_voltages,
    input logic i_clk,
    input logic i_rst_b
);

    enum logic [1:0] {
        CONVERT_LOW=2'h0,
        CONVERT_HIGH=2'h1,
        DWA=2'h2
    } state, next_state;

    logic [13:0]                   sar_counter;
    logic [$clog2(N_SAR_BITS)-1:0] sar_bit_counter;
    logic [N_SAR_BITS-1:0] dwa_pointer;
    logic                  previous_en_sar;

    // next state logic
    always_comb begin
        case (state)
            CONVERT_LOW  : next_state = (sar_counter == (rd.N_SAR_CYCLES - 1)) ? CONVERT_HIGH : CONVERT_LOW;
            CONVERT_HIGH : next_state = (sar_counter == (rd.N_SAR_CYCLES - 1)) && (sar_bit_counter == (N_SAR_BITS - 1)) ? DWA : CONVERT_LOW;
            DWA          : next_state = (sar_counter == (2 * (rd.N_SAR_CYCLES - 1))) ? CONVERT_LOW : DWA;
        endcase
    end

    always_ff @(posedge i_clk) begin
        if (!i_rst_b) begin
            state <= CONVERT_LOW;
            sar_counter <= 0;
            sar_bit_counter <= 0;
            dwa_pointer <= 0;
            previous_en_sar <= 0;
        end else begin
            previous_en_sar <= i_en_sar;
            if (i_en_sar && (state == next_state))
                sar_counter <= sar_counter + 1;
            else
                sar_counter <= 0;
            if (i_en_sar && (state == CONVERT_HIGH) && (next_state != CONVERT_HIGH))
                sar_bit_counter <= sar_bit_counter + 1;
            else if (i_en_sar && (state == DWA) && (next_state == CONVERT_LOW))
                sar_bit_counter <= 0;
        end
    end

endmodule
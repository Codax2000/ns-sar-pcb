module main_state_machine #(
    parameter N_SAR_BITS = 3
) (
    reg_if.RD rd,
    input logic i_clk,
    input logic i_rst_b,
    input logic i_start,
    output logic [2:0] o_main_state,
    output logic o_sample,
    output logic o_int1,
    output logic o_int2
);

    logic [13:0] nfft_counter;
    logic [15:0] current_state_counter;

    enum logic [2:0] {
        READY=3'h0,
        SAMPLE=3'h1,
        QUANTIZE=3'h2,
        INT1=3'h3,
        INT2=3'h4,
        STOP=3'h5
    } state, next_state;

    // next state logic
    always_comb begin
        case (state)
            READY : begin
                o_main_state = 3'h0;
                next_state = i_start ? SAMPLE : READY;
            end
            SAMPLE : begin
                o_main_state = 3'h1;
                next_state = (current_state_counter == (rd.N_SH_TOTAL_CYCLES - 1)) ? QUANTIZE : SAMPLE;
            end
            QUANTIZE : begin
                o_main_state = 3'h2;
                // stay in QUANTIZE for 4 * N_SAR_CYCLES - 1 for each SAR bit and 1 for DWA
                next_state = (current_state_counter == ((rd.N_SAR_CYCLES * (N_SAR_BITS + 1)) - 1)) ? INT1 : QUANTIZE;
            end
            INT1 : begin
                o_main_state = 3'h3;
                next_state = (current_state_counter == (rd.N_INT1_TOTAL_CYCLES - 1)) ? INT2 : INT1;
            end
            INT2 : begin
                o_main_state = 3'h4;
                next_state = (current_state_counter == (rd.N_INT2_TOTAL_CYCLES - 1)) ? 
                                 (nfft_counter == ((1 << rd.NFFT_POWER) - 1)) ? STOP : SAMPLE : INT2;
            end
            STOP : begin
                o_main_state = 3'h5;
                next_state = i_start ? STOP : READY;
            end
            default : begin
                o_main_state = 3'h0;
                next_state = READY;
            end
        endcase
    end

    assign o_sample = (state == SAMPLE) && (current_state_counter <= (rd.N_SH_ACTIVE_CYCLES - 1));
    assign o_int1   = (state == INT1)   && (current_state_counter <= (rd.N_INT1_ACTIVE_CYCLES - 1));
    assign o_int2   = (state == INT2)   && (current_state_counter <= (rd.N_INT2_ACTIVE_CYCLES - 1));

    always_ff @(posedge i_clk) begin
        if (!i_rst_b) begin
            state <= READY;
            current_state_counter <= 0;
            nfft_counter <= 0;
        end else begin
            state <= next_state;
            if ((state == INT2) && (next_state == READY))
                nfft_counter <= 0;
            else if ((state == INT2) && (next_state == SAMPLE))
                nfft_counter <= nfft_counter + 1;
            if (state != next_state)
                current_state_counter <= 0;
            else
                current_state_counter <= (current_state_counter + 1);
        end
    end

endmodule
import adc_regs_mod_pkg::*;

module main_state_machine (
    input logic i_clk,
    input logic i_rst,

    adc_regs_mod_pkg::adc_regs__out_t hwif_read,
    adc_regs_mod_pkg::adc_regs__in_t  hwif_rb,

    output logic o_sample,
    output logic o_int1,
    output logic o_int2,
    output logic o_incremental_reset,

    output logic o_start_sar,
    input  logic i_sar_done,
    output logic o_start_dwa,
    input  logic i_dwa_done
);

    logic [8:0]  active_passive_counter;
    logic [7:0]  osr_counter;
    logic [15:0] nfft_counter;

    logic reset_active_passive_counter;
    logic increment_active_passive_counter;
    logic increment_osr_counter;
    logic increment_nfft_counter;

    enum logic [2:0] {
        READY,
        SAMPLE,
        SAR_CONVERT,
        SAR_DWA,
        INT1,
        INT2,
        DONE
    } state, next_state;

    always_ff @(posedge i_clk) begin
        if (i_rst) begin
            active_passive_counter <= 0;
            osr_counter            <= 0;
            nfft_counter           <= 0;
        end
        else begin
            state <= next_state;

            if (reset_active_passive_counter)
                active_passive_counter <= 0;
            else
            if (increment_active_passive_counter)
                active_passive_counter <= active_passive_counter + 1;
        
            if (state == READY) begin
                osr_counter  <= 0;
                nfft_counter <= 0;
            end
            else begin
                if (increment_osr_counter)
                    osr_counter <= osr_counter + 1;
                if (increment_nfft_counter)
                    nfft_counter <= nfft_counter + 1;
            end
        end
    end

    always_comb begin : next_state_logic
        if (!hwif_read.ADC_CTRL.START_CONVERSION.value)
            next_state = READY;
        else begin
            case(state)
                READY  : next_state = sh_counter_sum == 0 ? SAR_CONVERT : SAMPLE;
                SAMPLE : begin
                    if (active_passive_counter == sh_counter_sum)
                        next_state = SAR_CONVERT;
                    else
                        next_state = SAMPLE;
                end
                SAR_CONVERT : begin
                    if (!i_sar_done)
                        next_state = SAR_CONVERT;
                    else if (hwif_read.FFT_CTRL.DWA_EN.value)
                        next_state = SAR_DWA;
                    else if (nfft_counter == 1 << hwif_read.FFT_CTRL.NFFT_POWER.value)
                        next_state = DONE;
                    else if (!hwif_read.FFT_CTRL.NOISE_SHAPING_EN.value) begin
                        next_state = SAMPLE;
                    end
                    else if (int1_counter_sum == 0) begin
                        if (int2_counter_sum == 0)
                            next_state = SAMPLE;
                        else
                            next_state = INT2;
                    end
                    else
                        next_state = INT1;
                end
                SAR_DWA : begin
                    if (!i_dwa_done)
                        next_state = SAR_DWA;
                    else if (nfft_counter == 1 << hwif_read.FFT_CTRL.NFFT_POWER.value)
                        next_state = DONE;
                    else if (!hwif_read.FFT_CTRL.NOISE_SHAPING_EN.value) begin
                        next_state = SAMPLE;
                    end
                    else if (int1_counter_sum == 0) begin
                        if (int2_counter_sum == 0)
                            next_state = SAMPLE;
                        else
                            next_state = INT2;
                    end
                    else
                        next_state = INT1;
                end
                INT1 : begin
                    if (active_passive_counter != int1_counter_sum)
                        next_state = INT1;
                    else if (int2_counter_sum == 0) begin
                        next_state = SAMPLE;
                    end
                    else
                        next_state = INT1;
                end
                INT2 : begin
                    if (active_passive_counter != int2_counter_sum)
                        next_state = INT2;
                    else
                        next_state = SAMPLE;
                end
            endcase
        end
    end : next_state_logic

endmodule
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
    logic [8:0]  sh_counter_sum;
    logic [8:0]  int1_counter_sum;
    logic [8:0]  int2_counter_sum;
    logic [7:0]  osr_counter;
    logic [15:0] nfft_counter;

    logic reset_active_passive_counter;
    logic increment_active_passive_counter;
    logic reset_osr_counter;
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

    assign reset_active_passive_counter = state != next_state;
    assign increment_active_passive_counter = state inside {SAMPLE, INT1, INT2};
    assign reset_osr_counter = (state == SAR_CONVERT) && (next_state != SAR_CONVERT) &&
                               (osr_counter == ((1 << hwif_read.FFT_CTRL.OSR_POWER.value) - 1));
    assign increment_osr_counter = (state == SAR_CONVERT) && (next_state != SAR_CONVERT) && (!reset_osr_counter);
    assign increment_nfft_counter = reset_osr_counter;

    assign o_sample = (state == SAMPLE) && (active_passive_counter < hwif_read.SH_CTRL.N_ACTIVE_CYCLES.value);
    assign o_int1   = (state == INT1)   && (active_passive_counter < hwif_read.INT1_CTRL.N_ACTIVE_CYCLES.value);
    assign o_int2   = (state == INT2)   && (active_passive_counter < hwif_read.INT2_CTRL.N_ACTIVE_CYCLES.value);
    assign o_start_sar = state == SAR_CONVERT;
    assign o_start_dwa = state == SAR_DWA;
    assign hwif_rb.ADC_CTRL.START_CONVERSION.hwclr = state == DONE;
    assign sh_counter_sum = hwif_read.SH_CTRL.N_ACTIVE_CYCLES.value     + hwif_read.SH_CTRL.N_PASSIVE_CYCLES.value - 1;
    assign int1_counter_sum = hwif_read.INT1_CTRL.N_ACTIVE_CYCLES.value + hwif_read.INT1_CTRL.N_PASSIVE_CYCLES.value - 1;
    assign int2_counter_sum = hwif_read.INT2_CTRL.N_ACTIVE_CYCLES.value + hwif_read.INT2_CTRL.N_PASSIVE_CYCLES.value - 1;
    
    always_ff @(posedge i_clk) begin
        if (i_rst) begin
            state                  <= READY;
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
                if (reset_osr_counter)
                    osr_counter <= 0;
                else
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
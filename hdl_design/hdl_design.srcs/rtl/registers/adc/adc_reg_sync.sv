// Module: adc_regs_reg_sync
// Instantiates CDC synchronizers for the CSR registers.
// Automatically generated from registers.rdl using PeakRDL.
import adc_regs_mod_pkg::*;
module adc_regs_reg_sync #(
	parameter N_SYNC_STAGES=2
) (
	input adc_regs__in_t hwif_in_sysclk,
	input adc_regs__in_t hwif_in_ifclk,
	output adc_regs__out_t hwif_out_sysclk,
	output adc_regs__out_t hwif_out_ifclk,
	input logic sysclk,
	input logic ifclk,
	input logic sysclk_rst,
	input logic ifclk_rst
);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_SH_CTRL_N_ACTIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.SH_CTRL.N_ACTIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.SH_CTRL.N_ACTIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_SH_CTRL_N_PASSIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.SH_CTRL.N_PASSIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.SH_CTRL.N_PASSIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_INT1_CTRL_N_ACTIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.INT1_CTRL.N_ACTIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.INT1_CTRL.N_ACTIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_INT1_CTRL_N_PASSIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.INT1_CTRL.N_PASSIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.INT1_CTRL.N_PASSIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_INT2_CTRL_N_ACTIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.INT2_CTRL.N_ACTIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.INT2_CTRL.N_ACTIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(8)
	) sync_INT2_CTRL_N_PASSIVE_CYCLES (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.INT2_CTRL.N_PASSIVE_CYCLES.value),
		.dest_data(hwif_out_sysclk.INT2_CTRL.N_PASSIVE_CYCLES.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(3)
	) sync_FFT_CTRL_OSR_POWER (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.OSR_POWER.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.OSR_POWER.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(4)
	) sync_FFT_CTRL_NFFT_POWER (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.NFFT_POWER.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.NFFT_POWER.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_FFT_CTRL_INCREMENTAL_MODE_EN (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.INCREMENTAL_MODE_EN.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.INCREMENTAL_MODE_EN.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_FFT_CTRL_NOISE_SHAPING_EN (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.NOISE_SHAPING_EN.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.NOISE_SHAPING_EN.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(2)
	) sync_FFT_CTRL_N_QUANTIZER_BITS (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.N_QUANTIZER_BITS.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.N_QUANTIZER_BITS.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_FFT_CTRL_DWA_EN (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.DWA_EN.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.DWA_EN.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(4)
	) sync_FFT_CTRL_DELAY_LINE_CTRL (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.FFT_CTRL.DELAY_LINE_CTRL.value),
		.dest_data(hwif_out_sysclk.FFT_CTRL.DELAY_LINE_CTRL.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_ADC_CTRL_START_CONVERSION (
		.src_clk(ifclk),
		.dest_clk(sysclk),
		.src_data(hwif_out_ifclk.ADC_CTRL.START_CONVERSION.value),
		.dest_data(hwif_out_sysclk.ADC_CTRL.START_CONVERSION.value),
		.dest_clk_rst(sysclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_ADC_CTRL_SYNC_RESET_RB (
		.src_clk(sysclk),
		.dest_clk(ifclk),
		.src_data(hwif_in_sysclk.ADC_CTRL.SYNC_RESET_RB.next),
		.dest_data(hwif_in_ifclk.ADC_CTRL.SYNC_RESET_RB.next),
		.dest_clk_rst(ifclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(4)
	) sync_ADC_CTRL_MAIN_STATE_RB (
		.src_clk(sysclk),
		.dest_clk(ifclk),
		.src_data(hwif_in_sysclk.ADC_CTRL.MAIN_STATE_RB.next),
		.dest_data(hwif_in_ifclk.ADC_CTRL.MAIN_STATE_RB.next),
		.dest_clk_rst(ifclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(15)
	) sync_CONVERSION_FLAGS_N_VALID_SAMPLES (
		.src_clk(sysclk),
		.dest_clk(ifclk),
		.src_data(hwif_in_sysclk.CONVERSION_FLAGS.N_VALID_SAMPLES.next),
		.dest_data(hwif_in_ifclk.CONVERSION_FLAGS.N_VALID_SAMPLES.next),
		.dest_clk_rst(ifclk_rst)
	);

	sync_nstage #(
		.N_SYNC_STAGES(N_SYNC_STAGES),
		.N_BITS(1)
	) sync_CONVERSION_FLAGS_PREVIOUS_CONVERSION_CORRUPTED (
		.src_clk(sysclk),
		.dest_clk(ifclk),
		.src_data(hwif_in_sysclk.CONVERSION_FLAGS.PREVIOUS_CONVERSION_CORRUPTED.next),
		.dest_data(hwif_in_ifclk.CONVERSION_FLAGS.PREVIOUS_CONVERSION_CORRUPTED.next),
		.dest_clk_rst(ifclk_rst)
	);

endmodule : adc_regs_reg_sync

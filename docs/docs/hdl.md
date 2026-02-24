# Digital Logic

ADCs need digital logic. This means a register interface for CSRs (control and status registers) and
a main state machine to control the conversion. It therefore means closing timing and rigorous
verification.

## RTL

## Verification
# Noise-Shaping SAR ADC – Verification Regression Test Plan

## 1. Smoke / Sanity Tests (Per-Commit)

- smoke_reset
  - Assert reset during idle and mid-conversion
  - Verify registers return to defaults
  - Ensure no X/Z propagation

- smoke_reg_access
  - Write/read all control registers
  - Check illegal accesses
  - Boundary value testing

- smoke_clock_div
  - Sweep clock divider
  - Verify timing scales correctly


## 2. Functional Correctness Tests

- ramp_monotonicity
  - Slow ramp input
  - No missing codes
  - Monotonic output
  - Correct SAR latency

- dc_levels
  - Multiple DC inputs
  - Check gain and offset error

- step_response
  - Large step input
  - Verify settling and transient response


## 3. Spectral / Performance Tests

- snr_nominal
  - Full-scale sine input
  - Measure SNR and ENOB
  - Assert SNR > spec

- thd_nominal
  - Near full-scale sine
  - Measure THD and SFDR
  - Assert harmonics < spec

- osr_sweep
  - Sweep OSR
  - Verify 2nd-order noise shaping slope (~15 dB/octave)

- dem_on_off_compare
  - Compare spectra with DEM on vs off
  - Verify harmonic reduction


## 4. Mode Coverage Tests

- incremental_vs_continuous
  - Compare both operating modes
  - Validate behavior vs theory

- filter_coeff_sweep
  - Sweep 2nd-order filter coefficients
  - Check stability and overflow


## 5. Boundary & Stress Tests

- analog_digital_boundary_stress
  - Inject jitter / metastability modeling
  - Verify no lockup or corruption

- spi_mid_conversion
  - Modify registers mid-conversion
  - Verify graceful handling

- warmup_behavior
  - Ensure warmup samples are discarded properly


## 6. Randomized Tests

- random_reg_sequence
  - Randomized mode and OSR switching
  - Constrained random register access

- random_input_waveform
  - Random sine amplitude/frequency/phase
  - Verify stability


## 7. Long-Run Stability

- long_run_stability
  - Extended simulation duration
  - Verify no drift or state corruption


-------------------------------------------------------

# Regression Tiers

Per-Commit (Fast):
- smoke_reset
- smoke_reg_access
- ramp_monotonicity
- dc_levels

Nightly:
- snr_nominal
- thd_nominal
- osr_sweep
- dem_on_off_compare
- filter_coeff_sweep

Weekly / Extended:
- analog_digital_boundary_stress
- random_reg_sequence
- long_run_stability

## FPGA Implementation

### Timing

### FPGA Resources

| Test  | Functional Coverage | Status | Description |
| ----- | ------------------- | ------ | ----------- |
| `test_dac_reset` | 0.0% | 0.0% | With both DACs running, reset DUT and check that both DACs are disabled on startup. |
| `test_dac_dc` | 0.0% | 0.0% | With both DACs in DC mode, randomize DACs and check that output codes are correct. |
| `test_dac_ac` | 0.0% | 0.0% | With one or both DACs in AC mode, randomize frequency and DSM enable. |
| `test_dac_en` | 0.0% | 0.0% | Enable both DACs in DC or AC mode, then disable one or both. Ensure only one output packet received. |
| `test_dac_dsm` | 0.0% | 0.0% | With at least one DAC in delta-sigma mode, check output to make sure delta-sigma modulator is running. |
| `test_adc_reset` | 0.0% | 0.0% | Check that ADC registers match reset values on boot. |
| `test_adc_mem`  | 0.0% | 0.0% | Check that for some number of FFT, OSR, and incremental enable, the correct number of ADC outputs is returned. |
| `test_adc_conversion` | 0.0% | 0.0% | Check that, for some number of FFT, OSR, and incremental controls, the conversion outputs are the same, given the analog models output the correct value. |
| `test_mem_readback` | 0.0% | 0.0% | Check that memory, when read back using random burst read access, is correctly read back. |
| `test_spi_burst` | 0.0% | 0.0% | Test SPI burst mode read and write accesses across a range of registers (e.g., configuring SH_CTRL, INT1_CTRL, INT2_CTRL, FFT_CTRL, ADC_CTRL consecutively) and verify register/data integrity. |
| `test_spi_double_buffered` | 0.0% | 0.0% | Test SPI access to double-buffered registers. Read and write shadow registers, verify that updates transfer to active registers only after a START_CONVERSION or synchronization point, and verify the read-back consistency. |

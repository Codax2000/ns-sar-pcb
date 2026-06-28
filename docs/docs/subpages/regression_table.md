| Test  | Functional Coverage | Status | Description |
| ----- | ------------------- | ------ | ----------- |
| `test_dac_reset` | 0.0% | 0.0% | With both DACs running, reset DUT and check that both DACs are disabled on startup. |
| `test_dac_dc` | 0.0% | 0.0% | With both DACs in DC mode, randomize DACs and check that output codes are correct. |
| `test_dac_ac` | 0.0% | 0.0% | With one or both DACs in AC mode, randomize frequency and DSM enable. |
| `test_dac_en` | 0.0% | 0.0% | Enable both DACs in DC or AC mode, then disable one or both. Ensure only one output packet received. |
| `test_dac_dsm` | 0.0% | 0.0% | With at least one DAC in delta-sigma mode, check output to make sure delta-sigma modulator is running. |
| `test_adc_reset` | 0.0% | 0.0% | Check that ADC registers match reset values on boot. |
| `test_adc_mem`  | 0.0% | 0.0% | Check that for some number of FFT, OSR, and incremental enable, the correct number of ADC outputs is returned. |

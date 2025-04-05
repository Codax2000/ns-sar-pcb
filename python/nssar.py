'''
Alex Knowlton
4/1/2025

Class definition for modeling a noise-shaping SAR ADC
using the Silva-Steensgard architecture, with an
optional reset
'''

from scipy.signal import iirfilter, windows, lfilter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pdb

class NSSAR:

    def __init__(self, n_quantizer_bits=3, cap_mismatch_sigma=0.05, \
                 n_fixed_point_bits=24, n_fractional_bits=16, filter_order=4,
                 vdd=1.0, vss=0, max_nfft=2**20, max_osr=256):
        '''
        set class with hardware constraints and initialize register fields
        with default functions
        '''
        self._reg = {
            'nfft': 2**12,
            'osr': 16,
            'fs': 100e6,
            'incremental_mode': True,
            'do_dwa': True,
            'reset_dwa': True,
            'offset_samples': 1500
        }
        normalized_fc = 1 / self._reg['osr']
        b, a = iirfilter(filter_order, normalized_fc, \
                         btype='lowpass', output='ba', ftype='butter')
        self._n_fractional_bits = n_fractional_bits
        self._n_fixed_point_bits = n_fixed_point_bits
        self._reg['filter_numerator'] = b
        self._reg['filter_denominator'] = a
        self._cp = np.random.normal(1, cap_mismatch_sigma, \
                                    2 ** n_quantizer_bits)
        self._cn = np.random.normal(1, cap_mismatch_sigma, \
                                    2 ** n_quantizer_bits)
        self._generate_loop_arrays()
        self._result_memory = np.zeros(max_nfft, dtype=int)
        self._max_osr = max_osr
        self._vrefp = vdd
        self._vrefn = vss

    def convert(self, signal_specs):
        '''
        Converts a list of dictionaries of the type below and stores them
        in memory
        {
            'amplitude': a_in,
            'frequency': f_in
            'phase': phi_in
        }
        '''
        print('Beginning DSM Loop')
        self._generate_control_signals()
        self._generate_input_signals(signal_specs)
        nfft_derived = self._reg['nfft'] * self._reg['osr']
        offset = self._reg['osr'] * self._reg['offset_samples']
        for i in range(offset + nfft_derived):
            self._calculate_integrator_to_quantizer(i)
            self._calculate_sample_to_quantizer(i)
            self._quantize(i)
            self._update_dwa(i)
            self._update_analog_integrators(i)
            self._update_incremental_integrators(i)
            self._step_iir_filter(i)
        self._write_data_to_memory()

    def write_register_value(self, key, value):
        '''
        writes a register value if the key is valid and if the value is valid
        if the key is not valid, throws an UnfoundRegisterError
        if the value is not valid, throws an IllegalRegisterValueError
        '''
        self._validate_register_write_value(key, value)
        self._reg[key] = value
        self._generate_loop_arrays()

    def read_register_value(self, key):
        '''
        if the register exists, return the value
        if the register does not exist, throw an UnfoundRegisterError
        '''
        self._validate_register_read_value(key)
        return self._reg[key]

    def read_output_data(self):
        '''
        Return nfft values from device memory as a Pandas Series
        with time-series indices
        '''
        return pd.Series(self._result_memory[:self._reg['nfft']], self._t) 

    def read_conversion_data(self):
        '''
        Return osr * (nfft + n_offset) values from the conversion as a Pandas
        DataFrame with time-series index
        '''
        output = pd.DataFrame()
        output['t'] = self._t
        output['U'] = self._u
        output['Qin_sample'] = self._qin_sample
        output['Qin_integ'] = self._qin_integ
        output['v_inp'] = self._vinp
        output['v_inn'] = self._vinn
        output['v_intp'] = self._vintp
        output['v_intn'] = self._vintn
        output['E'] = self._error
        output['I1'] = self._i1
        output['I2'] = self._i2
        output['V'] = self._v
        output['D1_inc'] = self._d1_incremental
        output['D2_inc'] = self._d2_incremental
        output['reset'] = self._reset
        output['sample_output'] = self._sample_output
        output['DWA_pointer'] = self._dwa_pointer
        output = output.set_index('t')
        return output

    def plot_output_fft(self, ax=None):
        '''
        Plot the FFT of the output and return a handle of the figure object
        on which it's plotted. If ax is none, create and set up a new figure
        and return it. If ax is not none, assume it's already set up and plot
        on that
        '''
        q_data = self._get_windowed_fft_data()
        T = self._reg['osr'] / self._reg['fs']
        freqs = np.fft.fftfreq(self._reg['nfft'], T)[1:1+(self._reg['nfft'] // 2)]
        freqs[-1] *= -1
        fft_pow = np.real(q_data * np.conj(q_data))
        i_max_pow = np.argmax(fft_pow[3:]) + 3  # bin smearing due to Blackman
        fft_pow /= fft_pow[i_max_pow]
        fft_pow_db = 10 * np.log10(fft_pow)
        if ax is None:
            fig, ax = plt.subplots()
            ax.set_xscale('log')
            ax.set_xlabel('Input Frequency')
            ax.set_ylabel('Output PSD')
            ax.set_title('Output FFT')
        else:
            fig = ax.get_figure()
        ax.plot(freqs[2:], fft_pow_db[2:])
        return fig

    def plot_quantizer_fft(self, ax=None):
        '''
        Plot the FFT of the output and return a handle of the figure object
        on which it's plotted. If ax is none, create and set up a new figure
        and return it. If ax is not none, assume it's already set up and plot
        on that
        '''
        q_data = self._get_windowed_fft_data(True)
        T = 1 / self._reg['fs']
        nfft_derived = self._reg['nfft'] * self._reg['osr']
        freqs = np.fft.fftfreq(nfft_derived, T)[1:1+(nfft_derived // 2)]
        freqs[-1] *= -1
        fft_pow = np.real(q_data * np.conj(q_data))
        i_max_pow = np.argmax(fft_pow[3:]) + 3  # bin smearing due to Blackman
        fft_pow /= fft_pow[i_max_pow]
        fft_pow_db = 10 * np.log10(fft_pow)
        if ax is None:
            fig, ax = plt.subplots()
            ax.set_xscale('log')
            ax.set_xlabel('Input Frequency')
            ax.set_ylabel('Quantizer PSD')
            ax.set_title('Quantizer FFT')
        else:
            fig = ax.get_figure()
        ax.plot(freqs[2:], fft_pow_db[2:])
        critical_frequency = self._reg['fs'] / (2 * self._reg['osr'])
        ax.axvline(x=critical_frequency, color='red', linestyle='--')
        return fig

    def plot_output_data(self, n_samples, ax=None):
        '''
        plots the output data in the interval (n_offset, n_offset + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted
        '''
        plot_data = self._result_memory[:n_samples]
        plot_time = self._t[self._sample_output]
        plot_time = plot_time[-self._reg['nfft']:]
        plot_time = plot_time[:n_samples]
        if ax is None:
            fig, ax = plt.subplots()
            ax.set_xlabel('Sample Time [s]')
            ax.set_ylabel('ADC Output')
        else:
            fig = ax.get_figure()
        ax.plot(plot_time, plot_data)
        return fig

    def get_sndr(self):
        '''
        Returns the SNDR of the last conversion. If no conversion has been
        done yet, return 0
        '''
        fft_data = self._get_windowed_fft_data()[2:]  # filter out DC data
        fft_pow = np.real(fft_data * np.conj(fft_data))
        i_max_power = np.argmax(fft_pow)
        signal_slice = np.arange(i_max_power-2, i_max_power+3)
        filt = np.zeros(fft_pow.shape[0], dtype=bool)
        filt[signal_slice] = True
        is_signal_indices = filt
        signal_power = np.sum(fft_pow[is_signal_indices])
        noise_power = np.sum(fft_pow[~is_signal_indices])
        sndr = signal_power / noise_power
        sndr_db = 10 * np.log10(sndr)
        return sndr_db

    def get_sfdr(self):
        '''
        Returns the SFDR of the last conversion. If no conversion has been
        done yet, return 0
        '''
        fft_data = self._get_windowed_fft_data()[2:]  # filter out DC data
        fft_pow = np.real(fft_data * np.conj(fft_data))
        i_max_power = np.argmax(fft_pow)
        noise_slice_to_signal = np.arange(i_max_power-2)
        noise_signal_to_fs = np.arange(i_max_power+3, fft_pow.shape[0])
        indices = np.zeros(fft_pow.shape[0], dtype=bool)
        is_noise_slice_low = indices
        is_noise_slice_low[noise_slice_to_signal] = True
        is_noise_slice_high = indices
        is_noise_slice_low[noise_signal_to_fs] = True
        signal_power = fft_pow[i_max_power]
        noise_power_low = fft_pow[is_noise_slice_low]
        noise_power_high = fft_pow[is_noise_slice_high]
        max_pow_low = np.max(noise_power_low)
        max_pow_high = np.max(noise_power_high)
        noise_power = np.max((max_pow_high, max_pow_low))
        sfdr = signal_power / noise_power
        sfdr_db = 10 * np.log10(sfdr)
        return sfdr_db

    def _fp_quantize(self, value):
        '''
        quantizes the input value to the internal (N, R) values
        '''
        N = self._n_fixed_point_bits
        R = self._n_fractional_bits
        max_value = 2 ** (N - 1) - 1
        min_value = -(2 ** (N - 1))
        value = value * (2 ** R)
        value = np.floor(value).astype(int)
        is_over_max = value > max_value
        is_under_min = value < min_value
        value[is_over_max] = max_value
        value[is_under_min] = min_value
        return value
    
    def _fp_add(self, a, b):
        pass

    def _fp_mult(self, a, b):
        pass

    def _generate_loop_arrays(self):
        '''
        generates loop arrays for IADC and DSM conversion
        '''
        # derived parameters
        T = 1 / self._reg['fs']
        n_total_samples = self._get_total_samples()
        self._t = np.arange(n_total_samples) * T
        self._error = np.zeros(self._t.shape)
        self._i1 = np.zeros(self._t.shape)
        self._i2 = np.zeros(self._t.shape)
        self._d1_incremental = np.zeros(self._t.shape)
        self._d2_incremental = np.zeros(self._t.shape)
        self._qin_sample = np.zeros(self._t.shape)
        self._qin_integ = np.zeros(self._t.shape)
        self._dwa_pointer = np.zeros(self._t.shape, dtype=int)
        self._v = np.zeros(self._t.shape, dtype=int)
        self._dac_output = np.zeros(self._t.shape)
        self._vinp = np.zeros(self._t.shape)
        self._vinn = np.zeros(self._t.shape)
        self._vintp = np.zeros(self._t.shape)
        self._vintn = np.zeros(self._t.shape)

    def _generate_control_signals(self):
        '''
        Generate reset and sample_output signals
        '''
        n_samples = self._get_total_samples()
        osr = self._reg['osr']
        i = np.arange(n_samples)
        incremental_reset = (i % osr == 0) & self._reg['incremental_mode']
        global_reset = i == 0
        self._reset = incremental_reset | global_reset
        self._sample_output = (i % osr) == (osr - 1)


    def _generate_input_signals(self, data):
        '''
        Generates input signal U and stores as a class variable
        '''
        self._u = self._t * 0
        for d in data:
            u = d['amplitude'] * \
                np.cos(2 * np.pi * d['frequency'] * self._t + d['phase'])
            self._u += u

    def _calculate_integrator_to_quantizer(self, i):
        '''
        calculate vintp and vintn to the quantizer
        '''
        vcm = (self._vrefp + self._vrefn) / 2
        if self._reset[i]:
            self._qin_integ[i] = 0
        else:
            self._qin_integ[i] = 2 * self._i1[i - 1] + self._i2[i - 1]
        self._vintp[i] = vcm + self._qin_integ[i] / 2
        self._vintn[i] = vcm - self._qin_integ[i] / 2

    def _calculate_sample_to_quantizer(self, i):
        '''
        calculate vinp and vinn to the quantizer
        '''
        self._qin_sample[i] = self._u[i]
        vcm = (self._vrefp + self._vrefn) / 2
        self._vinp[i] = vcm + self._qin_sample[i] / 2
        self._vinn[i] = vcm - self._qin_sample[i] / 2

    def _quantize(self, i):
        '''
        quantizer input with DWA, if applicable
        '''
        not_using_dwa = (i == 0) or (not self._reg['do_dwa'])
        reset_dwa_pointer = self._reset[i] and self._reg['do_dwa'] and \
            self._reg['reset_dwa']
        if (not_using_dwa or reset_dwa_pointer):
            pointer = 0
        else:
            pointer = self._dwa_pointer[i - 1]
        self._v[i], self._dac_output[i] = self._run_sar(i, pointer)
        self._error[i] = self._dac_output[i]

    def _update_dwa(self, i):
        '''
        Update DWA pointer by adding the last quantizer value
        '''
        pointer = self._dwa_pointer[i - 1]
        pointer += self._v[i]
        max_pointer_value = self._cp.shape[0]
        self._dwa_pointer[i] = pointer % max_pointer_value

    def _update_analog_integrators(self, i):
        if self._reset[i]:
            self._i1[i] = self._error[i]
            self._i2[i] = 0
        else:
            self._i1[i] = self._error[i] + self._i1[i - 1]
            self._i2[i] = self._i1[i - 1] + self._i2[i - 1]

    def _update_incremental_integrators(self, i):
        if self._reset[i]:
            self._d1_incremental[i] = self._v[i]
            self._d2_incremental[i] = self._d1_incremental[i]
        else:
            self._d1_incremental[i] = self._v[i] + self._d1_incremental[i - 1]
            self._d2_incremental[i] = self._d1_incremental[i] + \
                self._d2_incremental[i - 1]

    def _step_iir_filter(self, i):
        num = self._reg['filter_numerator']
        den = self._reg['filter_denominator']

    def _write_data_to_memory(self):
        adc_data = self._d2_incremental[self._sample_output]
        self._result_memory[:self._reg['nfft']] = adc_data[-self._reg['nfft']:]

    def _get_fft_frequencies(self, use_quantizer_data=False):
        '''
        Return frequencies of fft as frequency, not normalized to fs. If using
        quantizer, go up to fs / 2, else only go up to fs / (2 * osr)
        '''
        if use_quantizer_data:
            top_nfft_num = self._reg['osr'] * self._reg['nfft']
        else:
            top_nfft_num = self._reg['nfft']
        top_nfft_num = top_nfft_num // 2
        freqs = np.arange(top_nfft_num) + 1
        return self._reg['fs'] * freqs / (2 * top_nfft_num)

    def _get_windowed_fft_data(self, use_quantizer_data=False):
        '''
        Return windowed fft data, using the Blackman window,
        as power normalized to the fundamental tone(s)
        if not use_quantizer_data, use the output data
        '''
        if use_quantizer_data:
            top_nfft_num = self._reg['osr'] * self._reg['nfft']
            data = self._v[-top_nfft_num:]
        else:
            top_nfft_num = self._reg['nfft']
            data = self._result_memory[:top_nfft_num]
        fft_window = windows.blackman(top_nfft_num)
        windowed_data = fft_window * data
        return np.fft.fft(windowed_data)[1:(1 + top_nfft_num // 2)]

    def _get_total_samples(self):
        '''
        returns the total number of samples in the conversion
        '''
        return self._reg['osr'] * \
            (self._reg['nfft'] + self._reg['offset_samples'])
    
    def _run_sar(self, j, pointer):
        '''
        Actually runs SAR adc loop
        '''
        cp = self._cp
        cn = self._cn
        n_bits = int(np.log2(len(cp)))

        # roll capacitor values if using DWA
        cp = np.roll(cp, -pointer)
        cn = np.roll(cn, -pointer)

        # residue voltage for all conversions, at all points in conversion
        vresp = np.zeros(n_bits + 1)
        vresn = np.zeros(n_bits + 1)
        bits = np.zeros(n_bits, dtype=int)

        vcm = (self._vrefp + self._vrefn) / 2

        cap_values = np.zeros(2**n_bits) + vcm
        vresp[0] = self._vrefp - self._vinp[j]
        vresn[0] = self._vrefp - self._vinn[j]
        for i in range(n_bits):
            filt = self._vintp[j] + vresn[i] >= self._vintn[j] + vresp[i]
            bits[i] = 1 * filt
            cap_values = self._update_cap_values(cap_values, i, filt)
            inverted_cap_values = 1 - cap_values
            qp = np.sum(cp * (cap_values)) + np.sum(cp) * (vresp[0] - vcm)
            qn = np.sum(cn * (inverted_cap_values)) + np.sum(cn) * (vresn[0] - vcm)
            vresp[i + 1] = qp / np.sum(cp)
            vresn[i + 1] = qn / np.sum(cn)
        bits_calc = n_bits - 1
        positive_bits = bits_calc - np.where(bits == 1)[0]
        return np.sum(np.power(2, positive_bits)), vresn[n_bits] - vresp[n_bits]

    def _update_cap_values(self, cap_values, i, bit):
        '''
        Update capacitor voltages to either 1 or 0 depending on the SAR conversion
        '''
        # calculate slice to update
        n_bits = int(np.log2(cap_values.shape[0]))
        n_update_bits = 2**(n_bits - (i + 1))
        update_slice = np.where(cap_values == 0.5)[0]
        if bit:
            cap_values[update_slice[:n_update_bits]] = 1
        else:
            cap_values[update_slice[-(n_update_bits + 1):-1]] = 0
        return cap_values

    class UnfoundRegisterError(Exception):
        def __init__(self, register_name):
            super().__init__(f'Register name \'{register_name}\' not found')

    class IllegalRegisterValueError(Exception):
        def __init__(self, key, value):
            super().__init__(f'Value {value} illegal for register {key}')

    def _validate_register_write_value(self, key, value):
        '''
        Check that register write values are legal. If the key is not found,
        raise a new UnfoundRegisterError. If the value is not legal, raise a
        new IllegalRegisterValueError
        '''
        self._validate_register_key(key)
        is_legal_nfft_value = (key == 'nfft') and \
            (type(value) == type(1)) and \
            (value <= self._result_memory.shape[0])
        is_legal_osr_value = (key == 'osr') and (value <= self._max_osr)
        is_legal_fs = (key == 'fs') and (type(value) == type(1))
        is_legal_offset_samples = (key == 'offset_samples') and \
            (type(value) == type(1)) and value <= self._get_total_samples()
        is_legal_boolean_value = type(value) == type(True)
        is_legal_register_value = is_legal_nfft_value or is_legal_osr_value \
            or is_legal_fs or is_legal_offset_samples or is_legal_boolean_value
        if not is_legal_register_value:
            raise IllegalRegisterValueError(key, value)
        
    def _validate_register_key(self, key):
        '''
        Check that register read value is legal. If the key is not found,
        raise a new UnfoundRegisterError.
        '''
        if key not in self._reg.keys():
            raise UnfoundRegisterError(key)
'''
Alex Knowlton
4/1/2025

Class definition for modeling a noise-shaping SAR ADC
using the Silva-Steensgard architecture, with an
optional reset
'''

from scipy.signal import iirfilter, windows, lfilter
import numpy as np
import matplotlib.pyplot as plt

class NSSAR:

    def __init__(self, n_quantizer_bits=3, cap_mismatch_sigma=0.02, \
                 n_integer_bits=0, n_fractional_bits=0, filter_order=6,
                 vdd=1.2, vss=0, max_nfft=2**20):
        '''
        set class with hardware constraints and initialize register fields
        with default functions
        '''
        self._registers = {
            'nfft': 2**12,
            'osr': 32,
            'fs': 100e6,
            'incremental_mode': False,
            'do_dwa': True,
            'reset_dwa': False,
            'offset_samples': 1500
        }
        normalized_fc = 1 / (2 * self._registers['nfft'])
        b, a = iirfilter(filter_order, 2 * normalized_fc, \
                         btype='lowpass', output='ba', ftype='butter')
        self._n_fractional_bits = n_fractional_bits
        self._n_integer_bits = n_integer_bits
        b = self._fp_quantize(b)
        a = self._fp_quantize(a)
        self._registers['filter_numerator'] = b
        self._registers['filter_denominator'] = a
        self._cp = np.random.normal(1, cap_mismatch_sigma, \
                                    2 ** n_quantizer_bits)
        self._cn = np.random.normal(1, cap_mismatch_sigma, \
                                    2 ** n_quantizer_bits)
        self._generate_loop_arrays()
        self._result_memory = np.zeros(max_nfft, dtype=int)
        self._vrefp = vdd
        self._vrefn = vss
    
    def convert(self, signal_specs):
        '''
        Converts a list of dictionaries of the type below and stores them
        in memory
        '''
        self._generate_control_signals()
        self._generate_input_signals(signal_specs)
        nfft_derived = self._registers['nfft'] * self._registers['osr']
        offset = self._registers['osr'] * self._registers['offset_samples']
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
        pass

    def read_register_value(self, key):
        '''
        if the register exists, return the value
        if the register does not exist, throw an UnfoundRegisterError
        '''
        pass

    def read_output_data(self):
        '''
        Return nfft + n_offset values from device memory as a Pandas Series
        with time-series indices
        '''
        pass

    def read_conversion_data(self):
        '''
        Return osr * (nfft + n_offset) values from the conversion as a Pandas
        DataFrame with time-series index
        '''
        pass

    def plot_output_fft(self, ax=None):
        '''
        Plot the FFT of the output and return a handle of the figure object
        on which it's plotted. If ax is none, create and set up a new figure
        and return it. If ax is not none, assume it's already set up and plot
        on that
        '''
        pass

    def plot_quantizer_fft(self, ax=None):
        '''
        Plot the FFT of the output and return a handle of the figure object
        on which it's plotted. If ax is none, create and set up a new figure
        and return it. If ax is not none, assume it's already set up and plot
        on that
        '''
        pass

    def plot_output_data(self, n_samples, ax=None):
        '''
        plots the output data in the interval (n_offset, n_offset + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted
        '''
        pass

    def get_sndr(self):
        '''
        Returns the SNDR of the last conversion. If no conversion has been
        done yet, return 0
        '''
        pass

    def get_sfdr(self):
        '''
        Returns the SFDR of the last conversion. If no conversion has been
        done yet, return 0
        '''
        pass

    class UnfoundRegisterError(Exception):
        def __init__(self, register_name):
            super().__init__(f'Register name \'{register_name}\' not found')
    
    class IllegalRegisterValueError(Exception):
        def __init__(self, key, value):
            super().__init__(f'Value {value} illegal for register {key}')

    def _fp_quantize(self, value):
        pass

    def _generate_loop_arrays(self):
        pass

    def _generate_control_signals(self):
        pass

    def _generate_input_signals(self, data):
        pass

    def _calculate_integrator_to_quantizer(self, i):
        pass

    def _calculate_sample_to_quantizer(self, i):
        pass

    def _quantize(self, i):
        pass

    def _update_dwa(self, i):
        pass

    def _update_analog_integrators(self, i):
        pass

    def _update_incremental_integrators(self, i):
        pass

    def _step_iir_filter(self, i):
        pass

    def _write_data_to_memory(self):
        pass

    def _get_fft_frequencies(self, use_quantizer_data=False):
        '''
        Return frequencies of fft as frequency, not normalized to fs. If using
        quantizer, go up to fs / 2, else only go up to fs / (2 * osr)
        '''
        pass

    def _get_windowed_fft_data(self, use_quantizer_data=False):
        '''
        Return windowed fft data as power normalized to the fundamental tone(s)
        if not use_quantizer_data, use the output data
        '''
        pass
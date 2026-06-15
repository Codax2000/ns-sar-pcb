'''
Alex Knowlton
6/14/2026

Class definition for modeling a differential AC/DC sine wave generator with a DAC.
This includes a delta-sigma modulator to reduce quantization noise in AC mode and
differential outputs that can be either in AC or DC mode.
'''

class SineGenDAC:
    def __init__(self, n_dac_bits=8, n_cordic_bits=16, fs=100e6):
        '''
        set class with hardware constraints and initialize register fields
        with default functions
        '''
        self._reg = {
            'frequency': 0x0,
            'amplitude': 0xF,
            'dacp_mode': 'DC',
            'dacn_mode': 'DC',
            'dsm_enable': False,
            'dc_value': 0x0,
        }
    
    def set_frequency(self, frequency):
        if frequency < 0 or frequency > 2**4 - 1:
            raise ValueError("Frequency must be between 0 and 15")
        self._reg['frequency'] = frequency

    def set_amplitude(self, amplitude):
        if amplitude < 0 or amplitude > 2**4 - 1:
            raise ValueError("Amplitude must be between 0 and 15")
        self._reg['amplitude'] = amplitude

    def set_dac_mode(self, dac_number=0, mode='DC'):
        if mode not in ['DC', 'AC']:
            raise ValueError("DACP mode must be either DC or AC")
        if dac_number not in [0, 1]:
            raise ValueError("DAC number must be 0 or 1")
        if dac_number == 0:
            self._reg['dacp_mode'] = mode
        else:
            self._reg['dacn_mode'] = mode

    def set_dsm_enable(self, enable=True):
        self._reg['dsm_enable'] = enable

    def convert(self, n_samples):
        '''
        Runs DAC conversion using the set registers and returns the output data. in
        a pandas DataFrame with time-series index.
        '''
        pass

    def plot_output(self, n_samples, ax=None):
        '''
        Plots the DAC output data in the interval (n_offset, n_offset + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted
        '''
        pass

    def plot_output_fft(self, n_samples, ax=None):
        '''
        Plots the FFT of the DAC output data in the interval (n_offset, n_offset + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted. If it the axis is None, a new figure is created and returned.
        '''
        pass

    def get_filtered_output(self, n_samples):
        '''
        Returns the output data, like convert, but with a filter applied to the
        output that matches what would be implemented on PCB. This is meant to be
        passed into the ADC, as if after an anti-aliasing filter.
        '''
        pass

    def _calculate_phase(self, n_samples):
        '''
        Calculates the phase of the sine wave for the given number of samples.
        Calculation done in rotations (i.e. 0 to 1) and is used to generate the
        inputs to the CORDIC. Stores in the class variable _phase.
        '''
        pass

    def _calculate_cordic(self, phase):
        '''
        Calculates the sine and cosine of the _phase using the CORDIC algorithm.
        Stores in the class variables _sin and _cos.
        '''
        pass

    def _calculate_delta_sigma(self):
        '''
        Calculates the delta-sigma output for the _cos output of the CORDIC.
        '''
        pass
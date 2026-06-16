'''
Alex Knowlton
6/14/2026

Class definition for modeling a differential AC/DC sine wave generator with a DAC.
This includes a delta-sigma modulator to reduce quantization noise in AC mode and
differential outputs that can be either in AC or DC mode.
'''
import numpy as np
import pandas as pd
from numba import njit
import matplotlib.pyplot as plt

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
            'dacp_dc_value': 0x0,
            'dacn_dc_value': 0x0,
            'warmup_cycles': 1000
        }
        self._n_dac_bits = n_dac_bits
        self._n_cordic_bits = n_cordic_bits
        self._fs = fs
    
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
        Runs DAC conversion using the set registers and returns the output data in
        a pandas DataFrame.
        '''
        self._t = np.arange(n_samples) / self._fs
        self._calculate_phase(n_samples)
        self._calculate_cordic()

        if self._reg['dsm_enable']:
            self._quant, self._error = self._run_dsm_loop(self._cos, 
                                                          self._n_cordic_bits - self._n_dac_bits)
        else:
            self._quant = self._cos >> (self._n_cordic_bits - self._n_dac_bits)
            self._error = self._cos - (self._quant << (self._n_cordic_bits - self._n_dac_bits))
        self._quant_bar = (1 << self._n_dac_bits) - 1 - self._quant
        results = pd.DataFrame({
            'time_seconds': self._t
        })

        has_ac_mode = self._reg['dacp_mode'] == 'AC' or self._reg['dacn_mode'] == 'AC'

        results['phase']      = self._phase if has_ac_mode else 0
        results['cordic_sin'] = self._sin if has_ac_mode else 0
        results['cordic_cos'] = self._cos if has_ac_mode else 0
        results['dacp_output'] = self._quant if self._reg['dacp_mode'] == 'AC' else self._reg['dacp_dc_value']
        results['dacn_output'] = self._quant_bar if self._reg['dacn_mode'] == 'AC' else self._reg['dacn_dc_value']
        results['error'] = self._error if has_ac_mode else 0

        return results

    def plot_output(self, n_samples, ax=None):
        '''
        Plots the DAC output data in the interval (n_offset, n_offset + reg['warmup_cycles']
        on the given axis and returns a handle to the figure on which it is
        plotted. If ax is provided, plots on that axis and does nothing else.

        If ax is not provided, plots DAC output, labels axes, and returns a new figure.
        '''
        # Generate enough samples, including warmup cycles, then slice for plotting
        total_samples = n_samples + self._reg['warmup_cycles']
        data = self.convert(total_samples)
        plot_data = data.iloc[self._reg['warmup_cycles']:]

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure

        ax.plot(plot_data['time_seconds'], plot_data['dacp_output'], label='DACP Output')
        ax.plot(plot_data['time_seconds'], plot_data['dacn_output'], label='DACN Output')
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('DAC Output Value')
        ax.set_title('Sine Wave Generator DAC Output')
        ax.legend()
        ax.grid()

        return fig

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
        self._phase = np.arange(n_samples) * (1 << self._reg['frequency'])

    def _calculate_cordic(self):
        '''
        Calculates the sine and cosine of the _phase using the CORDIC algorithm.
        Stores in the class variables _sin and _cos.
        '''
        # TODO: use fixed-point CORDIC to calculate the sine and cosine
        self._sin = np.floor(np.sin(self._phase * np.pi * 2 / 0x10000) * (2**16))
        self._cos = np.floor(np.cos(self._phase * np.pi * 2 / 0x10000) * (2**16))

    @njit
    def _run_dsm_loop(u, shift):
        N = len(u)
        q = np.zeros(N)
        e = np.zeros(N)
        v = np.zeros(N, dtype=np.int64)

        for k in range(N):
            if k == 0:
                e_r = 0
                e_rr = 0
            elif k == 1:
                e_r = e[k - 1]
                e_rr = 0
            else:
                e_r = e[k - 1]
                e_rr = e[k - 2]

            q[k] = u[k] - e_rr + (2 * e_r)
            v[k] = int(q[k]) >> shift
            e[k] = v[k] - q[k]
            
        return v, e

def main():
    # Test 1: DAC output without Delta-Sigma Modulation
    print("Running SineGenDAC test without DSM...")
    dac_test_no_dsm = SineGenDAC()
    dac_test_no_dsm.set_frequency(0xC)
    dac_test_no_dsm.set_dac_mode(dac_number=0, mode='AC')
    
    n_cycles = 10000
    
    fig, ax = plt.subplots(figsize=(12, 7))
    dac_test_no_dsm.plot_output(n_cycles, ax=ax)
    ax.lines[-2].set_label('DACP Output (No DSM)') # Adjust label for previous plot
    ax.lines[-1].set_label('DACN Output (No DSM)') # Adjust label for previous plot

    # Test 2: DAC output with Delta-Sigma Modulation
    print("Running SineGenDAC test with DSM...")
    dac_test_with_dsm = SineGenDAC()
    dac_test_with_dsm.set_frequency(0xC)
    dac_test_with_dsm.set_dac_mode(dac_number=0, mode='AC')
    dac_test_with_dsm.set_dsm_enable(enable=True)
    
    dac_test_with_dsm.plot_output(n_cycles, ax=ax)
    ax.lines[-2].set_label('DACP Output (With DSM)')
    ax.lines[-1].set_label('DACN Output (With DSM)')

    ax.set_title(f'Sine Wave Generator DAC Output (Freq=0xC, {n_cycles} cycles)')
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    plt.show()
    print("Test complete.")

if __name__ == "__main__":
    main()

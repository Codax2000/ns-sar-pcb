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
import pdb

class SineGenDAC:
    def __init__(self, n_dac_bits=8, n_cordic_bits=16, fs=100e6, vdd=3.3):
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
        self._vdd = vdd
    
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
        self._t = np.arange(n_samples + self._reg['warmup_cycles']) / self._fs
        self._calculate_phase(n_samples + self._reg['warmup_cycles'])
        self._calculate_cordic()

        if self._reg['dsm_enable']:
            self._quant, self._error = _run_dsm_loop(self._cos, 
                                                     self._n_cordic_bits - self._n_dac_bits)
            self._quant_bar = ((2**self._n_dac_bits) - 1) - self._quant
        else:
            self._quant = self._cos >> (self._n_cordic_bits - self._n_dac_bits)
            self._error = self._cos - (self._quant << (self._n_cordic_bits - self._n_dac_bits))
            self._quant_bar = -self._quant
            
            # set to unsigned by adding Qrange / 2
            self._quant     += (2 ** (self._n_dac_bits - 1))
            self._quant_bar += (2 ** (self._n_dac_bits - 1))

        self._results = pd.DataFrame({
            'time_seconds': self._t
        })

        has_ac_mode = self._reg['dacp_mode'] == 'AC' or self._reg['dacn_mode'] == 'AC'

        self._results['phase']      = self._phase if has_ac_mode else 0
        self._results['cordic_sin'] = self._sin if has_ac_mode else 0
        self._results['cordic_cos'] = self._cos if has_ac_mode else 0
        self._results['dacp_output'] = self._quant     if self._reg['dacp_mode'] == 'AC' else self._reg['dacp_dc_value']
        # self._results['dacp_output'] *= self._vdd / ((1 << self._n_dac_bits) - 1) 
        self._results['dacn_output'] = self._quant_bar if self._reg['dacn_mode'] == 'AC' else self._reg['dacn_dc_value']
        # self._results['dacn_output'] *= self._vdd / ((1 << self._n_dac_bits) - 1) 
        self._results['error'] = self._error if has_ac_mode else 0

        return self._results.copy()

    def plot_output(self, n_samples, ax=None):
        '''
        Plots the DAC output data in the interval (n_offset, n_offset + reg['warmup_cycles']
        on the given axis and returns a handle to the figure on which it is
        plotted. If ax is provided, plots on that axis and does nothing else.

        If ax is not provided, plots DAC output, labels axes, and returns a new figure.
        '''
        # Generate enough samples, including warmup cycles, then slice for plotting
        total_samples = n_samples + self._reg['warmup_cycles']

        if not hasattr(self, '_results'):
            raise ValueError('Must run conversion before plotting is attempted')

        data = self._results
        plot_data = data.iloc[self._reg['warmup_cycles']:total_samples]

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

    def plot_output_fft(self, n_samples, ax=None, n_fft_samples=None):
        '''
        Plots the FFT of the DAC output data in the interval (warmup_cycles, warmup_cycles + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted. If it the axis is None, a new figure is created and returned.
        If n_fft_samples is not provided, it defaults to n_samples.
        '''
        if n_fft_samples is None:
            n_fft_samples = n_samples

        if not hasattr(self, '_results'):
            raise ValueError('Must run conversion before plotting is attempted')

        data = self._results
        # Slice data to exclude warmup cycles and take n_samples for FFT
        plot_data = data.iloc[self._reg['warmup_cycles'] : self._reg['warmup_cycles'] + n_samples]

        # Use n_fft_samples for FFT calculation, zero-padding if necessary
        fft_input_dacp = np.fft.fft(plot_data['dacp_output'], n=n_fft_samples)
        fft_input_dacn = np.fft.fft(plot_data['dacn_output'], n=n_fft_samples)
        
        # Calculate frequency bins
        fs = self._fs
        freq_bins = np.fft.fftfreq(n_fft_samples, d=1/fs)

        # Take the magnitude and select the positive frequencies
        fft_output_dacp = np.abs(fft_input_dacp) / n_samples
        fft_output_dacn = np.abs(fft_input_dacn) / n_samples
        
        positive_freq_mask = freq_bins >= 0
        freq_bins = freq_bins[positive_freq_mask]
        fft_output_dacp = fft_output_dacp[positive_freq_mask]
        fft_output_dacn = fft_output_dacn[positive_freq_mask]

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure

        ax.semilogy(freq_bins, fft_output_dacp, label='DACP FFT')
        ax.semilogy(freq_bins, fft_output_dacn, label='DACN FFT')
        
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Amplitude')
        ax.set_title('Sine Wave Generator DAC Output FFT')
        ax.legend()
        ax.grid()

        return fig

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
        self._sin = np.floor(np.sin(self._phase * np.pi * 2 / 0x10000) * (2**15)).astype(int)
        self._cos = np.floor(np.cos(self._phase * np.pi * 2 / 0x10000) * (2**15)).astype(int)

@njit
def _run_dsm_loop(u, shift):
    N = len(u)
    q = np.zeros(N)
    e = np.zeros(N)
    e_prev = 0.0 # Initialize previous error
    e_prev_prev = 0.0 # Initialize previous-previous error

    for k in range(N):
        # Second-order error-feedback delta-sigma modulator
        # q[k] = u[k] + e[k-1] + e[k-2] -- for non-error feedback
        # For error feedback, error is signal - quantized_signal
        # e[k] = q[k] - v[k] (where v[k] is quantized output)
        # To make it second order error feedback, we integrate the error twice.
        # The integrator output is fed back.
        # x[k] = u[k] - y[k]
        # i1[k] = i1[k-1] + x[k]
        # i2[k] = i2[k-1] + i1[k]
        # y[k] = i2[k] 
        # In our case, u is the input signal, and we want to quantize it.
        # Let's use the standard formulation for error feedback:
        # error_integrator1[k] = error_integrator1[k-1] + input_signal[k] - quantized_output[k-1]
        # error_integrator2[k] = error_integrator2[k-1] + error_integrator1[k]
        # quantized_output[k] = error_integrator2[k]

        # Let's simplify and use the structure from common second-order DSM implementations.
        # The general form for a second-order error feedback loop:
        # y[k] = input[k] - feedback[k]
        # integrator1[k] = integrator1[k-1] + y[k]
        # integrator2[k] = integrator2[k-1] + integrator1[k]
        # quantized_output[k] = integrator2[k]
        # The feedback is typically related to the quantized output.
        # A common structure for second-order error feedback is:
        # integrator1[k] = integrator1[k-1] + input_signal[k] - quantized_output[k-1]
        # integrator2[k] = integrator2[k-1] + integrator1[k]
        # quantized_output[k] = integrator2[k]

        # Let's stick to a simpler formulation that can be derived from the first-order one
        # by adding another integrator for the error.
        # error_signal = u[k] - (v[k] << shift)
        # q[k] represents the input to the quantizer.
        # In a second order error feedback:
        # input_to_integrator1 = u[k] - (v[k-1] << shift)  <- error from previous step
        # integrator1_output = integrator1_output_prev + input_to_integrator1
        # input_to_integrator2 = integrator1_output
        # integrator2_output = integrator2_output_prev + input_to_integrator2
        # v[k] = integrator2_output >> shift (this is the quantized output)
        # e[k] = integrator2_output - (v[k] << shift) # This definition of error might be tricky

        # A more direct implementation of a second-order error feedback loop:
        # Let e1 be the output of the first integrator and e2 be the output of the second.
        # Input to first integrator: u[k] - quantized_output[k-1] (error from previous quantizer output)
        # Output of first integrator: e1[k] = e1[k-1] + (u[k] - quantized_output[k-1])
        # Input to second integrator: e1[k]
        # Output of second integrator: e2[k] = e2[k-1] + e1[k]
        # Quantized output: quantized_output[k] = floor(e2[k] / (1 << shift))
        
        # Let's use the 'e' array to store the output of the second integrator (which is the input to the quantizer)
        # and 'e_r' to store the output of the first integrator.
        # We need to keep track of the previous quantized output.
        
        prev_quantized = v[k-1] if k > 0 else 0

        # Calculate the current error term to be fed into the first integrator
        current_error_term = u[k] - (prev_quantized << shift)
        
        # Update the first integrator's state
        e_r = e_prev + current_error_term
        
        # Update the second integrator's state
        e[k] = e_prev_prev + e_r
        
        # Quantize the output of the second integrator
        v[k] = int(e[k]) >> shift
        
        # Store current states for the next iteration
        e_prev = e_r
        e_prev_prev = e[k]

    # The error calculation needs to be consistent with the quantized output 'v'.
    # If v[k] is the quantized value, then the overall error fed back should be related to e[k].
    # For simulation purposes, we can define the error as the difference between the input to the quantizer (e[k])
    # and the actual quantized output (v[k] << shift).
    final_error = e - (v << shift)
        
    return v, final_error
    dac.set_dac_mode(dac_number=1, mode='AC')
    
    n_cycles = 10000
    n_plot_cycles = 6000
    results = dac.convert(n_cycles)

    fig_tseries, ax_tseries = plt.subplots(figsize=(12, 7))
    dac.plot_output(n_plot_cycles, ax=ax_tseries)
    ax_tseries.lines[-2].set_label('DACP Output (No DSM)') # Adjust label for previous plot
    ax_tseries.lines[-1].set_label('DACN Output (No DSM)') # Adjust label for previous plot

    # Test 2: DAC output with Delta-Sigma Modulation (Second Order)
    print("Running SineGenDAC test with DSM (Second Order)...")
    dac.set_dsm_enable(enable=True)
    results = dac.convert(n_cycles)
    
    dac.plot_output(n_plot_cycles, ax=ax_tseries)
    ax_tseries.lines[-2].set_label('DACP Output (With DSM)')
    ax_tseries.lines[-1].set_label('DACN Output (With DSM)')

    ax_tseries.set_title(f'Sine Wave Generator DAC Output (Freq=0xC, {n_cycles} cycles)')
    ax_tseries.legend()
    ax_tseries.grid(True)
    fig_tseries.tight_layout()
    fig_tseries.savefig('./dac_dsm_tseries.png')
    print("Time series plot complete.")

    # Test 3: FFT plot
    print("Running SineGenDAC test for FFT plot...")
    # Use the same DAC object with DSM enabled
    n_fft_samples = 1024 # Number of samples for FFT
    fig_fft, ax_fft = plt.subplots(figsize=(10, 6))
    dac.plot_output_fft(n_samples=n_cycles, ax=ax_fft, n_fft_samples=n_fft_samples)
    ax_fft.set_title(f'Sine Wave Generator DAC Output FFT (Freq=0xC, {n_cycles} cycles, {n_fft_samples} FFT points)')
    fig_fft.tight_layout()
    fig_fft.savefig('./dac_dsm_fft.png')
    print("FFT plot complete.")

    print("All tests complete.")
    print(results.head())
    # pdb.set_trace()


if __name__ == "__main__":
    main()

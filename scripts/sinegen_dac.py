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

from CORDIC import CORDIC
from fp_logic import fp_quantize # Import fp_quantize

class SineGenDAC:
    def __init__(self, n_dac_bits=1, n_cordic_bits=16, fs=100e6, vdd=3.3):
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
            'warmup_cycles': 1000,
            'osr': 8
        }
        self._n_dac_bits = n_dac_bits
        self._n_cordic_bits = n_cordic_bits
        self._fs = fs
        self._vdd = vdd
        self._cordic = CORDIC(n_rotations=n_cordic_bits, n_x=n_cordic_bits, r_x=n_cordic_bits - 1, n_z=n_cordic_bits, r_z=n_cordic_bits - 1)
    
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
            # The _run_dsm_loop function expects the input signal and the shift value.
            # _cos is the input signal, and (self._n_cordic_bits - self._n_dac_bits) is the shift value.
            self._quant, self._error = _run_dsm_loop(self._cos, self._n_cordic_bits - self._n_dac_bits)
        else:
            self._quant = self._cos >> (self._n_cordic_bits - self._n_dac_bits)
            self._error = self._cos - (self._quant << (self._n_cordic_bits - self._n_dac_bits))
        
        # Generate inverse sine wave
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

    def plot_output_fft(self, ax=None, add_osrline=False):
        '''
        Plots the FFT of the DAC output data in the interval (n_offset, n_offset + n_samples)
        on the given axis and returns a handle to the figure on which it is
        plotted. If it the axis is None, a new figure is created and returned.
        '''
        if not hasattr(self, '_results'):
            raise ValueError('Must run conversion before plotting is attempted')

        # Use the number of samples available after warmup for FFT
        n_samples_for_fft = len(self._results) - self._reg['warmup_cycles']
        
        # Extract data after warmup cycles
        data_for_fft = self._results.iloc[self._reg['warmup_cycles']:]
        
        # Subtract DC offset (full-scale / 2) before FFT
        # Full scale is 2^n_dac_bits
        full_scale = 2**(self._n_dac_bits - 1)
        dc_offset = full_scale / 2.0
        dacp_no_dc = data_for_fft['dacp_output'] - dc_offset

        # Apply Blackman window
        window = np.blackman(n_samples_for_fft)
        windowed_dacp = dacp_no_dc * window

        # Perform FFT
        fft_output_dacp = np.fft.fft(windowed_dacp)
        self._fft_data = fft_output_dacp

        # Calculate frequency bins
        fs = self._fs
        freq_bins = np.fft.fftfreq(n_samples_for_fft, d=1/fs)

        # Convert to dB-full-scale
        # Scale by 2/N for two-sided spectrum magnitude, then convert to dBFS
        # dBFS = 20 * log10(Magnitude / FullScale)
        fft_magnitude_dacp_db = 20 * np.log10(np.abs(fft_output_dacp) * 2 / (full_scale * n_samples_for_fft))
        
        # Select positive frequencies
        positive_freq_mask = freq_bins >= 0
        freq_bins = freq_bins[positive_freq_mask]
        fft_magnitude_dacp_db = fft_magnitude_dacp_db[positive_freq_mask]

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.set_xscale('log') # Set x-axis to log scale for new figures
        else:
            fig = ax.figure

        ax.plot(freq_bins, fft_magnitude_dacp_db, label='DACP FFT')

        if add_osrline:
            osr = self._reg.get('osr', 64)
            cutoff_freq = (fs / 2) / osr
            ax.axvline(
                x=cutoff_freq, 
                color='r', 
                linestyle='--', 
                linewidth=1.5,
                label=f'$OSR={self._reg['osr']}$, $f_{{max}}={np.round(self._fs / 2 / self._reg['osr'] / 1e6, 3)}$ MHz'
            )
        
        ax.set_xlabel('Frequency [Hz]')
        ax.set_ylabel('Magnitude [dBFS]')
        ax.set_title('Sine Wave Generator DAC Output FFT')
        ax.legend()
        ax.grid(True, which="both", ls="-") # Use both major and minor grids

        return fig

    def get_sqnr_db(self):
        '''
        Calculates the Signal-to-Quantization-Noise Ratio (SQNR) in dB from the 
        calculated FFT data. Captures window smearing across 5 bins (peak +/- 2).
        '''
        # TODO: Break out calculating the FFT from plot_output_fft into a standalone helper function.
        if not hasattr(self, '_fft_data'):
            raise ValueError("plot_output_fft must be run first to populate FFT data.")

        # 1. Get the raw full FFT data (including negative frequencies)
        fft_data = self._fft_data
        N = len(fft_data)
        
        # 2. Only look at the positive frequencies (excluding DC at index 0)
        # Starting at index 3 prevents a high DC offset from being picked up as the signal peak
        # Want to avoid DC smearing as well
        pos_fft = fft_data[3:N//2]
        
        # 3. Find the peak bin location in the positive frequency spectrum
        # We add 1 to offset back to the original fft_data indexing
        peak_idx = np.argmax(np.abs(pos_fft)) + 1
        
        # 4. Calculate power spectrum (magnitude squared)
        power_spectrum = np.abs(fft_data) ** 2
        
        # 5. Extract Signal Power: Sum the peak bin and 2 bins on either side
        signal_bins = np.arange(peak_idx - 2, peak_idx + 3)
        signal_power = np.sum(power_spectrum[signal_bins])
        
        # 6. Extract Noise Power: Sum all positive frequencies, excluding DC and the signal bins
        all_pos_bins = np.arange(4, N//(2*self._reg['osr']))
        noise_power = np.sum(power_spectrum[all_pos_bins]) - signal_power
        
        # 7. Calculate SQNR in decibels
        if noise_power == 0:
            return float('inf') # Perfect quantization/no noise edge case
            
        sqnr_db = 10 * np.log10(signal_power / noise_power)
        return sqnr_db

    def get_filtered_output(self):
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
        self._phase = np.arange(n_samples) * (1 << self._reg['frequency']) * 17

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
    '''
    Runs the delta-sigma modulator loop to decimate the input signal.
    Args:
        u (np.array): The input signal (quantized values).
        shift (int): The number of bits to shift for decimation.
    Returns:
        tuple: A tuple containing:
            - v (np.array): The decimated output signal.
            - e (np.array): The quantization error.
    '''
    N = len(u)
    q = np.zeros(N)
    e = np.zeros(N)
    v = np.zeros(N, dtype=np.int64)

    for k in range(N):
        if k == 0:
            e_r  = 0
            e_rr = 0
        elif k == 1:
            e_r = -e[k - 1]
            e_rr = 0
        else:
            e_r  = -e[k - 1]
            e_rr =  e[k - 2]

        q[k] = u[k] + e_rr + (2 * e_r)
        v[k] = int(q[k]) >> shift
        e[k] = (v[k] << shift) - q[k]
        
    return v, e

def main():
    # Test 1: DAC output without Delta-Sigma Modulation
    print("Running SineGenDAC test without DSM...")
    dac = SineGenDAC()
    dac.set_frequency(0x7)
    dac.set_amplitude(0xC)
    dac.set_dac_mode(dac_number=0, mode='AC')
    dac.set_dac_mode(dac_number=1, mode='AC')
    
    n_cycles = 2**12
    n_plot_cycles = 250
    dac.convert(n_cycles)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    dac.plot_output(n_plot_cycles, ax=ax1)
    dac.plot_output_fft(ax=ax2)
    sqnr_no_dsm = dac.get_sqnr_db()
    ax1.lines[-2].set_label('DACP Output (No DSM)') # Adjust label for previous plot
    ax1.lines[-1].set_label('DACN Output (No DSM)') # Adjust label for previous plot

    # Test 2: DAC output with Delta-Sigma Modulation
    print("Running SineGenDAC test with DSM...")
    dac.set_dsm_enable(enable=True)
    dac.convert(n_cycles)
    
    dac.plot_output(n_plot_cycles, ax=ax1)
    dac.plot_output_fft(ax=ax2, add_osrline=True)
    sqnr_dsm = dac.get_sqnr_db()
    ax1.lines[-2].set_label('DACP Output (With DSM)')
    ax1.lines[-1].set_label('DACN Output (With DSM)')

    ax2.lines[-3].set_label(f'SQNR={np.round(sqnr_no_dsm, 3)}, NO DSM')
    ax2.lines[-2].set_label(f'SQNR={np.round(sqnr_dsm, 3)}, WITH DSM')

    ax1.set_title(f'Sine Wave Generator DAC Output ({n_cycles} cycles)')
    ax1.legend()
    ax2.legend()
    ax1.grid()
    ax2.grid()
    ax2.set_xscale('log') # Set x-axis to log scale for new figures
    fig.tight_layout()
    fig.savefig('./dac_dsm_tseries.png')
    print("Test complete.")


if __name__ == "__main__":
    main()

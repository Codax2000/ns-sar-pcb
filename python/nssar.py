'''
Alex Knowlton
3/24/2025

Simulation for a noise-shaping 2nd order SAR ADC with 1st-order DEM
'''


import numpy as np
import matplotlib.pyplot as plt


def main():
    '''
    Main simulation loop
    '''
    # circuit/testing parameters
    quantizer_bits = 3
    sigma = 0.02
    use_mismatch = True
    fs = 10**8 # 100 MHz for now
    prime = 139
    vdd = 1
    vss = 0
    vcm = (vdd - vss) / 2

    # control registers
    osr = 64
    nfft = 2**10
    incremental_mode = False
    use_dwa = False
    n_offset = 10000

    # derived parameters
    T = 1 / fs
    nfft_derived = nfft * osr
    fin = fs * prime / nfft_derived
    a_in = vdd * 10 ** (-1 / 20)  # input amplitude: -1 dBFS

    cp1 = get_cap_array(quantizer_bits, sigma, use_mismatch)
    cn1 = get_cap_array(quantizer_bits, sigma, use_mismatch)

    # time signal
    t = T * np.arange(n_offset * osr + nfft_derived)

    # input signal
    U = a_in * np.cos(2 * np.pi * fin * t)

    # analog integrators
    W1 = np.zeros(t.shape)
    W2 = np.zeros(t.shape)

    # digital integrators
    D1 = np.zeros(t.shape, dtype=int)
    D2 = np.zeros(t.shape, dtype=int)

    # SAR quantizer inputs
    Qin_sample = np.zeros(t.shape)
    Qin_integ = np.zeros(t.shape)

    # residue sampling
    residue = np.zeros(t.shape)

    # boolean signals, useful for logic development later
    reset = np.zeros(t.shape, dtype=bool)
    sample_output = np.zeros(t.shape, dtype=bool)
    dwa_pointer = np.zeros(t.shape, dtype=int)

    # quantizer output
    V = np.zeros(t.shape)
    E = np.zeros(t.shape)

    # differential input signals
    vinp = np.zeros(t.shape)
    vinn = np.zeros(t.shape)
    vintp = np.zeros(t.shape)
    vintn = np.zeros(t.shape)

    # downsampled output waveform
    final_sample = np.zeros(t.shape)

    # IADC loop
    for i in range(t.shape[0]):
        cycle = i % osr
        reset[i] = cycle == 0
        sample_output[i] = cycle == osr - 1
        if reset[i]:
            Qin_integ[i] = 0
        else:
            Qin_integ[i] = W1[i - 1] + W2[i - 1]

        Qin_sample[i] = U[i]
        
        vintp[i] = vcm + Qin_integ[i] / 2
        vintn[i] = vcm - Qin_integ[i] / 2
        vinp[i] = vcm + Qin_sample[i] / 2
        vinn[i] = vcm - Qin_sample[i] / 2
        





def get_cap_array(n_bits, sigma, use_mismatch):
    '''
    Returns an array of 2^n_bits capacitor values drawn from a
    normal distribution with a standard deviation of sigma
    '''
    if use_mismatch:
        return np.random.normal(1, sigma, 2**n_bits)
    else:
        return np.ones(2**n_bits)

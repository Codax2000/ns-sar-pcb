'''
Alex Knowlton
3/24/2025

Simulation for a noise-shaping 2nd order SAR ADC with 1st-order DEM
'''


import numpy as np
import matplotlib.pyplot as plt
import pdb


def main():
    '''
    Main simulation loop
    '''
    # circuit/testing parameters
    quantizer_bits = 3
    sigma = 0.02
    use_mismatch = False
    fs = 10**8 # 100 MHz for now
    prime = 139
    vdd = 1
    vss = 0
    vcm = (vdd - vss) / 2

    # control registers
    osr = 64
    nfft = 2**8
    incremental_mode = False
    use_dwa = False
    n_offset = 1000

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
        print(f'Cycle {i}')
        cycle = i % osr
        reset[i] = ((cycle == 0) and incremental_mode) or i == 0
        sample_output[i] = (cycle == osr - 1) or not incremental_mode

        # update integrators
        if reset[i]:
            W1[i] = 0
            W2[i] = 0
        else:
            W1[i] = W1[i - 1] + E[i - 1]
            W2[i] = W2[i - 1] + W1[i - 1]

        if reset[i]:
            Qin_integ[i] = 0
        else:
            Qin_integ[i] = 2 * W1[i] + W2[i]

        Qin_sample[i] = U[i]
        
        vintp[i] = vcm + Qin_integ[i] / 2
        vintn[i] = vcm - Qin_integ[i] / 2
        vinp[i] = vcm + Qin_sample[i] / 2
        vinn[i] = vcm - Qin_sample[i] / 2
        # pdb.set_trace()
        V[i], E[i] = quantize(vinp[i], vinn[i], vintp[i], vintn[i])

    pdb.set_trace()
    plt.subplot(2, 1, 1)
    plt.plot(V[0:400])
    plt.plot(U[0:400])
    plt.subplot(2, 1, 2)
    plt.loglog(np.fft.fft(V[-nfft_derived:]))
    plt.show()


def get_cap_array(n_bits, sigma, use_mismatch):
    '''
    Returns an array of 2^n_bits capacitor values drawn from a
    normal distribution with a standard deviation of sigma
    '''
    if use_mismatch:
        return np.random.normal(1, sigma, 2**n_bits)
    else:
        return np.ones(2**n_bits)


def quantize(vip, vin, vintp, vintn):
    '''
    single-bit quantizer function
    '''
    U = vip - vin
    W = vintp - vintn
    V = 1 if (U + W) > 0 else -1
    E = U - V
    return V, E


def sar_quantize(vip, vin, vintp, vintn, cp, cn, vrefp=1, vrefn=0, dwa_pointer=0):
    '''
    SAR quantizer function using two integrators and cap update functions
    also uses positive and negative reference voltages for more accurate numbers
    additionally, user can set the DWA pointer to shift the update voltages
    for DEM
    '''
    n_bits = int(np.log2(len(cp)))
    n_conversions = len(vip)

    # digital output values
    dout = np.zeros(vip.shape, dtype=int)

    # residue voltage for all conversions, at all points in conversion
    vresp = np.zeros((n_bits + 1, n_conversions))
    vresn = np.zeros((n_bits + 1, n_conversions))
    bits = np.zeros((n_bits, n_conversions), dtype=int)

    vcm = (vrefp + vrefn) / 2

    cap_voltages = np.zeros(cp.shape) + vcm
    vresp[0, :] = vrefp - vip
    vresn[0, :] = vrefp - vin
    pdb.set_trace()
    for i in range(n_bits):
        filt = vintp + vresn[i + 1, :] >= vintn + vresp[i + 1, :]
        bits[i, filt] = vrefp
        bits[i, ~filt] = vrefn
        pdb.set_trace()



if __name__ == '__main__':
    sar_quantize(np.array([0.6, 0.7]), np.array([0.4, 0.3]), -0.05, 0.05, np.array([1, 1, 1, 1]), np.array([1, 1, 1, 1]))
    # main()
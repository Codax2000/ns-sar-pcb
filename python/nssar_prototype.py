'''
Alex Knowlton
3/24/2025

Simulation for a noise-shaping 2nd order SAR ADC with 1st-order DEM
'''


import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import iirfilter, lfilter, windows
from scipy.fft import fft
import pdb


def adc_loop():
    '''
    Main simulation loop
    '''
    # circuit/testing parameters
    quantizer_bits = 3
    sigma = 0.02
    use_mismatch = False
    fs = 10**8 # 100 MHz for now
    prime = 97
    vdd = 1
    vss = 0
    vcm = (vdd - vss) / 2

    # control registers
    osr = 16
    nfft = 2**12
    incremental_mode = True
    use_dwa = True
    reset_dwa = True
    n_offset = 10000 if not incremental_mode else 0

    # derived parameters
    T = 1 / fs
    nfft_derived = nfft * osr
    fin = fs * prime / nfft_derived
    a_in = 0.4  # vdd * 10 ** (-6 / 20)

    # calculate filter coefficients
    normalized_fc = 1 / (osr)
    b, a = iirfilter(10, normalized_fc, btype='lowpass', output='ba', ftype='butter')

    # calculate mismatched capacitor arrays if using mismatch, all 1 otherwise
    cp = get_cap_array(quantizer_bits, sigma, use_mismatch)
    cn = get_cap_array(quantizer_bits, sigma, use_mismatch)
    pdb.set_trace()

    # time signal
    t = T * np.arange(n_offset + nfft_derived)

    # input signal
    U = a_in * np.cos(2 * np.pi * fin * t)
    # U = U * 0 + 0.8
    E = np.zeros(t.shape)

    # analog integrators
    I1 = np.zeros(t.shape)
    I2 = np.zeros(t.shape)

    # digital integrators
    D1_continuous = np.zeros(t.shape, dtype=int)
    D1_incremental = np.zeros(t.shape, dtype=int)
    D2_incremental = np.zeros(t.shape, dtype=int)

    # SAR quantizer inputs
    Qin_sample = np.zeros(t.shape)
    Qin_integ = np.zeros(t.shape)

    # boolean signals, useful for logic development later
    reset = np.zeros(t.shape, dtype=bool)
    sample_output = np.zeros(t.shape, dtype=bool)
    dwa_pointer = np.zeros(t.shape, dtype=int)  # don't use this yet

    # quantizer output
    V = np.zeros(t.shape)
    dac_output = np.zeros(t.shape)

    # differential input signals
    vinp = np.zeros(t.shape)
    vinn = np.zeros(t.shape)
    vintp = np.zeros(t.shape)
    vintn = np.zeros(t.shape)
    # IADC loop
    for i in range(t.shape[0]):
        # sample input
        reset[i] = ((i % osr) == 0 and incremental_mode) or (i == 0)
        sample_output[i] = (i % osr) == (osr - 1)
        Qin_sample[i] = U[i]

        # calculate integrator input to quantizer
        if (reset[i] or (i == 0)):
            Qin_integ[i] = 0
        else:
            Qin_integ[i] = 2 * I1[i - 1] + I2[i - 1]
        
        # convert to differential voltages
        vintp[i] = vcm + Qin_integ[i] / 2 
        vintn[i] = vcm - Qin_integ[i] / 2
        vinp[i] = vcm + Qin_sample[i] / 2
        vinn[i] = vcm - Qin_sample[i] / 2
        
        # quantize with DWA
        if ((i == 0) or (not use_dwa) or (reset[i] and use_dwa and reset_dwa)):
            pointer = 0
        else:
            pointer = dwa_pointer[i - 1]
        V[i], dac_output[i] = sar_quantize(vinp[i], vinn[i], vintp[i], vintn[i], cp, cn, pointer)
        E[i] = dac_output[i]
        pointer += V[i]
        dwa_pointer[i] = pointer % (2 ** quantizer_bits)
        # pdb.set_trace()
        # V[i] = quantize(vinp[i], vinn[i], vintp[i], vintn[i])
        # E[i] = U[i] - V[i]
        # update analog integrators
        if (reset[i] or (i == 0)):
            I1[i] = E[i]
            I2[i] = 0
        else:
            I1[i] = E[i] + I1[i - 1]
            I2[i] = I1[i - 1] + I2[i - 1]
        
        # update digital integrators
        if (reset[i] or (i == 0)):
            D1_incremental[i] = V[i]
            D2_incremental[i] = D1_incremental[i]
        else:
            D1_incremental[i] = V[i] + D1_incremental[i - 1]
            D2_incremental[i] = D1_incremental[i] + D2_incremental[i - 1]

    incremental_out = D2_incremental[sample_output] * 1 / (2 * osr * (osr + 1)) - ((2 ** quantizer_bits - 1) / (2 ** quantizer_bits))
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(incremental_out[-nfft:], linewidth=0.5)
    plt.subplot(2, 1, 2)
    fft_vals = fft(incremental_out[-nfft:])
    fft_pow = np.real(fft_vals * np.conj(fft_vals))
    fft_pow_trimmed = fft_pow[1:1 + (nfft // 2)]
    fft_pow_trimmed[-1] /= 2
    fft_pow_db = 10 * np.log10(fft_pow_trimmed)
    freq = np.arange(1, (nfft // 2) + 1) * fs / nfft
    plt.plot(freq, fft_pow_db, linewidth=0.5)
    plt.figure()
    V = V - (2 ** quantizer_bits - 1) / 2
    vfilt = lfilter(b, a, V[-nfft_derived:], axis=0)
    continuous_out = vfilt[sample_output[-nfft_derived:]]
    plt.subplot(3, 1, 1)
    fft_window = windows.hann(nfft_derived)
    fft_data = fft_window * vfilt
    plt.loglog(np.abs(fft(V[-nfft_derived:])))
    plt.subplot(3, 1, 2)
    fft_window = windows.blackman(nfft_derived)
    fft_data = fft_window * vfilt[-nfft_derived:]
    plt.loglog(np.abs(fft(fft_data)))
    plt.subplot(3, 1, 3)
    vfilt_out = vfilt[-nfft_derived:]
    vfilt_out = vfilt_out[sample_output[-nfft_derived:]]
    fft_window = windows.blackman(nfft)
    fft_data = fft_window * vfilt_out
    fft_to_plot = np.abs(fft(fft_data))
    plt.loglog(fft_to_plot[:(nfft//2)])
    pdb.set_trace()


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
    return V


def sar_quantize(vip, vin, vintp, vintn, cp, cn, dwa_pointer=0):
    '''
    SAR quantizer function using two integrators and cap update functions
    also uses positive and negative reference voltages for more accurate numbers
    additionally, user can set the DWA pointer to shift the update voltages
    for DEM
    '''
    n_bits = int(np.log2(len(cp)))
    vrefp = 1
    vrefn = 0

    # roll capacitor values if using DWA
    cp = np.roll(cp, -dwa_pointer)
    cn = np.roll(cn, -dwa_pointer)

    # residue voltage for all conversions, at all points in conversion
    vresp = np.zeros(n_bits + 1)
    vresn = np.zeros(n_bits + 1)
    bits = np.zeros(n_bits, dtype=int)

    vcm = (vrefp + vrefn) / 2

    cap_values = np.zeros(2**n_bits) + vcm
    vresp[0] = vrefp - vip
    vresn[0] = vrefp - vin
    for i in range(n_bits):
        filt = vintp + vresn[i] >= vintn + vresp[i]
        bits[i] = 1 * filt
        cap_values = update_cap_values(cap_values, i, filt)
        inverted_cap_values = 1 - cap_values
        qp = np.sum(cp * (cap_values)) + np.sum(cp) * (vresp[0] - vcm)
        qn = np.sum(cn * (inverted_cap_values)) + np.sum(cn) * (vresn[0] - vcm)
        vresp[i + 1] = qp / np.sum(cp)
        vresn[i + 1] = qn / np.sum(cn)
    bits_calc = n_bits - 1
    positive_bits = bits_calc - np.where(bits == 1)[0]
    return np.sum(np.pow(2, positive_bits)), vresn[n_bits] - vresp[n_bits]


def update_cap_values(cap_values, i, bit):
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


def plot_sar_conversion():
    vin = np.arange(-1, 1.001, 0.001)
    vres = np.zeros(vin.shape)
    dout = np.zeros(vin.shape)
    vcm = 0.5
    caps = np.ones(8)
    for i in range(len(vin)):
        vp = vin[i] / 2 + vcm
        vn = -vin[i] / 2 + vcm
        d, v = sar_quantize(vp, vn, 0, 0, caps, caps, 0)
        dout[i] = d
        vres[i] = v
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(vin, dout)
    plt.grid()
    plt.title('SAR Quantization Across Voltage')
    plt.ylabel('Digital Output')
    plt.subplot(2, 1, 2)
    plt.plot(vin, vres)
    plt.xlabel('$V_{in}$')
    plt.ylabel('$V_{res}$')
    plt.grid()


def main():
    '''
    Main loop
    '''
    plot_sar_conversion()
    adc_loop()
    plt.show()


if __name__ == '__main__':
    main()
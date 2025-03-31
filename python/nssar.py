'''
Alex Knowlton
3/24/2025

Simulation for a noise-shaping 2nd order SAR ADC with 1st-order DEM
'''


import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, freqz
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
    prime = 17
    vdd = 1
    vss = 0
    vcm = (vdd - vss) / 2

    # control registers
    osr = 8
    nfft = 2**11
    incremental_mode = False
    use_dwa = False
    n_offset = 10000

    # derived parameters
    T = 1 / fs
    nfft_derived = nfft * osr
    fin = fs * prime / nfft_derived
    a_in = vdd * 10 ** (-6 / 20)  # input amplitude: -1 dBFS

    # calculate filter coefficients
    normalized_fc = prime / nfft_derived
    b, a = butter(2, normalized_fc, btype='low', analog=False)

    # calculate mismatched capacitor arrays if using mismatch, all 1 otherwise
    cp = get_cap_array(quantizer_bits, sigma, use_mismatch)
    cn = get_cap_array(quantizer_bits, sigma, use_mismatch)

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
        print(f'Cycle {i}')
        # sample input
        Qin_sample[i] = U[i]

        # calculate integrator input to quantizer
        if (i == 0):
            Qin_integ[i] = 0
        else:
            Qin_integ[i] = 2 * I1[i - 1] + I2[i - 1]
        
        # convert to differential voltages
        vintp[i] = vcm + Qin_integ[i] / 2
        vintn[i] = vcm - Qin_integ[i] / 2
        vinp[i] = vcm + Qin_sample[i] / 2
        vinn[i] = vcm - Qin_sample[i] / 2
        
        # quantize with DWA
        V[i], dac_output[i] = sar_quantize(vinp[i], vinn[i], vintp[i], vintn[i], cp, cn, 0)
        E[i] = dac_output[i]
        # pdb.set_trace()
        # V[i] = quantize(vinp[i], vinn[i], vintp[i], vintn[i])
        # E[i] = U[i] - V[i]
        # update analog integrators
        if (i == 0):
            I1[i] = E[i]
            I2[i] = 0
        else:
            I1[i] = E[i] + I1[i - 1]
            I2[i] = I1[i - 1] + I2[i - 1]

    plt.figure()

    fft_pow = np.fft.fft(V[-nfft_derived:])
    fft_pow = np.conj(fft_pow) * fft_pow
    fft_pow_no_dc = fft_pow[1:(1+nfft_derived // 2)]
    fft_pow_no_dc_db = 10 * np.log10(fft_pow_no_dc)
    plt.semilogx(fft_pow_no_dc_db)


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
    caps = np.ones(16)
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
    # plot_sar_conversion()
    adc_loop()
    plt.show()


if __name__ == '__main__':
    main()
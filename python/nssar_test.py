from nssar import NSSAR
import pdb
import numpy as np


def test_fft_plots():
    sar = NSSAR(cap_mismatch_sigma=0.1)
    sar.write_register_value('do_dwa', False)
    fs = 100e6
    prime = 97
    nfft = 2**12
    signal_specs = [
        {
            'amplitude': 0.4,
            'frequency': fs * prime / (16 * nfft),
            'phase': 0
        }
    ]
    sar.convert(signal_specs)
    fig_data = sar.plot_output_data(1000)
    fig_fft = sar.plot_quantizer_fft()
    fig_output_fft = sar.plot_output_fft()
    fig_data.savefig('./img/quantizer_data.png')
    fig_fft.savefig('./img/quantizer_fft.png')
    fig_output_fft.savefig('./img/output_fft.png')
    sndr = sar.get_sndr()
    sfdr = sar.get_sfdr()
    print(f'SAR SNDR: {np.round(sndr, 2)} dB')
    print(f'SAR SFDR: {np.round(sfdr, 2)} dB')


def test_dwa():
    sar = NSSAR(cap_mismatch_sigma=0.1)
    fs = 100e6
    prime = 97
    nfft = 2**12
    signal_specs = [
        {
            'amplitude': 0.4,
            'frequency': fs * prime / (16 * nfft),
            'phase': 0
        }
    ]
    sar.convert(signal_specs)
    sndr = list()
    sfdr = list()
    sndr.append(sar.get_sndr())
    sfdr.append(sar.get_sfdr())
    sar.write_register_value('reset_dwa', False)
    sar.convert(signal_specs)
    sndr.append(sar.get_sndr())
    sfdr.append(sar.get_sfdr())
    sar.write_register_value('do_dwa', False)
    sar.convert(signal_specs)
    sndr.append(sar.get_sndr())
    sfdr.append(sar.get_sfdr())
    print(sndr)
    print(sfdr)


def main():
    test_fft_plots()
    test_dwa()


if __name__ == '__main__':
    main()
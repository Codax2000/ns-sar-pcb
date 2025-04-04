from nssar import NSSAR
import pdb


def test_fft_plots():
    sar = NSSAR()
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


def main():
    test_fft_plots()


if __name__ == '__main__':
    main()
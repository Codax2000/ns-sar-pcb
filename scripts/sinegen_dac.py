"""Differential DAC values and voltages from a scaled cosine.
"""

from __future__ import annotations

import unittest

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numba import njit

from cordic import cordic_rotate
from fp_array import FixedPointArray


BLACKMAN_HALF_WIDTH = 3
DEFAULT_OSR = 32


def _check_n_samples(n_samples: int) -> None:
    """Raise unless n_samples is a positive int."""
    if isinstance(n_samples, bool) or not isinstance(n_samples, int):
        received = type(n_samples).__name__
        raise TypeError(f"n_samples must be an int, got {received}")
    if n_samples < 1:
        raise ValueError(f"n_samples must be positive, got {n_samples}")


def _check_frequency(frequency: int) -> None:
    """Raise unless frequency is an int from 0 to 65535."""
    if isinstance(frequency, bool) or not isinstance(frequency, int):
        received = type(frequency).__name__
        raise TypeError(f"frequency must be an int, got {received}")
    if frequency < 0 or frequency > 65535:
        raise ValueError(
            f"frequency must be between 0 and 65535, got {frequency}"
        )


def _check_amplitude_scale(amplitude_scale: int) -> None:
    """Raise unless amplitude_scale is an int from 0 to 15."""
    if isinstance(amplitude_scale, bool) or not isinstance(
        amplitude_scale, int
    ):
        received = type(amplitude_scale).__name__
        raise TypeError(
            f"amplitude_scale must be an int, got {received}"
        )
    if amplitude_scale < 0 or amplitude_scale > 15:
        raise ValueError(
            "amplitude_scale must be between 0 and 15, "
            f"got {amplitude_scale}"
        )


def _check_amplitude(amplitude: int) -> None:
    """Raise unless amplitude is an int from 0 to 15."""
    if isinstance(amplitude, bool) or not isinstance(amplitude, int):
        received = type(amplitude).__name__
        raise TypeError(f"amplitude must be an int, got {received}")
    if amplitude < 0 or amplitude > 15:
        raise ValueError(
            f"amplitude must be between 0 and 15, got {amplitude}"
        )


def _check_dac_mode(mode: str, channel: str) -> None:
    """Raise unless mode is 'AC' or 'DC'."""
    if not isinstance(mode, str):
        received = type(mode).__name__
        raise TypeError(f"{channel} mode must be a str, got {received}")
    if mode not in ("AC", "DC"):
        raise ValueError(f"{channel} mode must be AC or DC, got {mode}")


def _check_dc_value(value: int, channel: str) -> None:
    """Raise unless value is an int from 0 to 255."""
    if isinstance(value, bool) or not isinstance(value, int):
        received = type(value).__name__
        raise TypeError(f"{channel} DC value must be an int, got {received}")
    if value < 0 or value > 255:
        raise ValueError(
            f"{channel} DC value must be between 0 and 255, got {value}"
        )


def _saturate(values: np.ndarray) -> np.ndarray:
    """Clamp integers to signed 8 bits."""
    return np.clip(values, -128, 127).astype(np.int64)


@njit
def _modulate_dsm(
    samples: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Quantize to signed 8 bits and return the values and feedback error."""
    shift = 8
    low = -128
    high = 127
    count = samples.shape[0]
    quantized = np.empty(count, dtype=np.int64)
    error = np.empty(count, dtype=np.int64)
    for index in range(count):
        if index == 0:
            previous = 0
            older = 0
        elif index == 1:
            previous = -error[0]
            older = 0
        else:
            previous = -error[index - 1]
            older = error[index - 2]
        accumulator = samples[index] + older + (2 * previous)
        truncated = accumulator >> shift
        if truncated > high:
            dac_integer = high
        elif truncated < low:
            dac_integer = low
        else:
            dac_integer = truncated
        quantized[index] = dac_integer
        # Opposite of the truncation error.
        error[index] = (dac_integer << shift) - accumulator
    return quantized, error


def _truncate(cosine: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Drop 8 bits and return the signed values and the error."""
    values = _saturate(np.asarray(cosine, dtype=np.int64) >> 8)
    error = cosine - (values << 8)
    return values, error


def _select_mode(
    mode: str, ac_values: np.ndarray, dc_value: int
) -> np.ndarray:
    """Return the AC samples or a constant DC array of the same length."""
    if mode == "AC":
        return np.asarray(ac_values, dtype=np.int64)
    return np.full(ac_values.shape, dc_value, dtype=np.int64)


def generate_dac_values(
    n_samples: int,
    frequency: int = 0,
    amplitude_scale: int = 8,
    amplitude: int = 15,
    dsm_enable: bool = False,
    dacp_mode: str = "DC",
    dacn_mode: str = "DC",
    dacp_dc_value: int = 0,
    dacn_dc_value: int = 0,
    vdd: float = 3.3,
) -> pd.DataFrame:
    """Return the DACP and DACN values and voltages for each clock.

    Call it with a register dictionary, for example
    ``generate_dac_values(4096, **registers)``.

    Parameters
    ----------
    n_samples : int
        Number of clocks.
    frequency : int, optional
        Phase step added each clock, from 0 to 65535. Default is 0.
    amplitude_scale : int, optional
        Scale from 0 to 15. The cosine is about scale/15 of full scale.
        Default is 8.
    amplitude : int, optional
        The cosine is shifted right by 15 minus this value. Default is 15.
    dsm_enable : bool, optional
        True runs the delta-sigma modulator. False truncates by 8 bits.
        Default is False.
    dacp_mode : str, optional
        ``"AC"`` uses the cosine. ``"DC"`` holds ``dacp_dc_value``.
        Default is ``"DC"``.
    dacn_mode : str, optional
        ``"AC"`` uses the negated cosine. ``"DC"`` holds
        ``dacn_dc_value``. Default is ``"DC"``.
    dacp_dc_value : int, optional
        DACP code from 0 to 255 in DC mode. Default is 0.
    dacn_dc_value : int, optional
        DACN code from 0 to 255 in DC mode. Default is 0.
    vdd : float, optional
        Supply in volts. Voltage is this value times the code divided
        by 256. Default is 3.3.

    Returns
    -------
    pandas.DataFrame
        Columns ``phase``, ``cosine``, ``dacp_value``, ``dacn_value``,
        ``dacp_voltage``, ``dacn_voltage``, and ``error``.

    Raises
    ------
    TypeError
        If an argument has the wrong type.
    ValueError
        If a count, scale, mode, or code is out of range.
    """
    _check_n_samples(n_samples)
    _check_frequency(frequency)
    _check_amplitude_scale(amplitude_scale)
    _check_amplitude(amplitude)
    _check_dac_mode(dacp_mode, "dacp")
    _check_dac_mode(dacn_mode, "dacn")
    _check_dc_value(dacp_dc_value, "dacp")
    _check_dc_value(dacn_dc_value, "dacn")
    # Unsigned 16-bit accumulator, then the signed reading of those bits.
    phase = (
        np.arange(n_samples, dtype=np.uint64) * np.uint64(frequency)
    ) & np.uint64(0xFFFF)
    phase = phase.astype(np.uint16)
    angles = FixedPointArray.from_mantissas(
        phase.astype(np.int16), 16, 16
    )
    cosine = np.asarray(
        cordic_rotate(amplitude_scale, angles).get_mantissas(),
        dtype=np.int64,
    )
    cosine = cosine >> (15 - amplitude)
    if dsm_enable:
        dac_signed, error = _modulate_dsm(cosine)
    else:
        dac_signed, error = _truncate(cosine)
    dacp_values = _select_mode(
        dacp_mode, dac_signed + 128, dacp_dc_value
    )
    dacn_values = _select_mode(
        dacn_mode, _saturate(-dac_signed) + 128, dacn_dc_value
    )
    return pd.DataFrame({
        "phase": phase,
        "cosine": cosine,
        "dacp_value": dacp_values,
        "dacn_value": dacn_values,
        "dacp_voltage": dacp_values * vdd / 256,
        "dacn_voltage": dacn_values * vdd / 256,
        "error": error,
    })


def _check_results(results: pd.DataFrame) -> None:
    """Raise unless results is a DataFrame."""
    if not isinstance(results, pd.DataFrame):
        received = type(results).__name__
        raise TypeError(f"results must be a DataFrame, got {received}")


def _check_column(results: pd.DataFrame, column: str) -> None:
    """Raise unless results contains column."""
    _check_results(results)
    if column not in results.columns:
        raise ValueError(f"results must include {column}")


def _check_warmup_samples(warmup_samples: int, n_rows: int) -> None:
    """Raise unless warmup_samples leaves at least one row."""
    if isinstance(warmup_samples, bool) or not isinstance(
        warmup_samples, int
    ):
        received = type(warmup_samples).__name__
        raise TypeError(
            f"warmup_samples must be an int, got {received}"
        )
    if n_rows < 1:
        raise ValueError(f"results must contain at least 1 row, got {n_rows}")
    if warmup_samples < 0 or warmup_samples >= n_rows:
        raise ValueError(
            "warmup_samples must be between 0 and "
            f"{n_rows - 1}, got {warmup_samples}"
        )


def _check_osr(osr: int) -> None:
    """Raise unless osr is a positive int."""
    if isinstance(osr, bool) or not isinstance(osr, int):
        received = type(osr).__name__
        raise TypeError(f"osr must be an int, got {received}")
    if osr < 1:
        raise ValueError(f"osr must be a positive int, got {osr}")


def _check_sample_rate(fs: float) -> None:
    """Raise unless fs is a positive real sample rate."""
    if isinstance(fs, bool) or not isinstance(fs, (int, float)):
        received = type(fs).__name__
        raise TypeError(f"fs must be a real number, got {received}")
    if fs <= 0:
        raise ValueError(f"fs must be positive, got {fs}")


def _calculate_dacp_spectrum(
    results: pd.DataFrame, warmup_samples: int
) -> np.ndarray:
    """Return the Blackman FFT of DACP after skipping warmup clocks."""
    _check_column(results, "dacp_value")
    _check_warmup_samples(warmup_samples, len(results))
    dacp = np.asarray(
        results["dacp_value"].iloc[warmup_samples:], dtype=np.float64
    )
    centered = dacp - 128.0
    window = np.blackman(centered.size)
    return np.fft.fft(centered * window)


def _find_band_edge_bin(count: int, osr: int) -> int:
    """Return the last FFT bin included in the noise sum."""
    _check_osr(osr)
    nyquist = count // 2
    last = count // (2 * osr)
    if last <= BLACKMAN_HALF_WIDTH:
        raise ValueError(
            f"band does not clear the DC leakage bins, got osr {osr}"
        )
    return min(last, nyquist)


def _calculate_sqnr(spectrum: np.ndarray, osr: int) -> float:
    """Return the in-band SQNR of one windowed spectrum."""
    count = len(spectrum)
    last_bin = _find_band_edge_bin(count, osr)
    power = np.abs(spectrum) ** 2
    guard = BLACKMAN_HALF_WIDTH
    search = np.arange(guard + 1, last_bin + 1)
    peak = int(search[np.argmax(power[search])])
    signal_bins = np.arange(peak - guard, peak + guard + 1)
    signal_bins = signal_bins[
        (signal_bins >= 0) & (signal_bins <= count // 2)
    ]
    noise_bins = search[~np.isin(search, signal_bins)]
    signal_power = float(np.sum(power[signal_bins]))
    noise_power = float(np.sum(power[noise_bins]))
    if noise_power == 0:
        return float("inf")
    return float(10 * np.log10(signal_power / noise_power))


def calculate_sqnr_db(
    results: pd.DataFrame,
    osr: int = DEFAULT_OSR,
    warmup_samples: int = 1000,
) -> float:
    """Return the in-band signal-to-quantization-noise ratio in dB.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`generate_dac_values`.
    osr : int, optional
        Band edge is half the sample rate divided by this value.
        Default is 32. 1 keeps the band through Nyquist.
    warmup_samples : int, optional
        Leading clocks skipped so the modulator can settle. Default
        is 1000.

    Returns
    -------
    float
        SQNR in dB. Infinity when the noise power is zero.

    Raises
    ------
    TypeError
        If ``osr`` or ``warmup_samples`` has the wrong type.
    ValueError
        If the band, warmup, or table is unusable.
    """
    spectrum = _calculate_dacp_spectrum(results, warmup_samples)
    return _calculate_sqnr(spectrum, osr)


def plot_output(
    results: pd.DataFrame,
    fs: float,
    n_samples: int,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot DACP and DACN values against time.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`generate_dac_values`.
    fs : float
        Sample rate in hertz.
    n_samples : int
        Number of clocks to plot from the start of ``results``.
    ax : matplotlib.axes.Axes or None, optional
        Axis to draw on. A new figure is created when omitted.

    Returns
    -------
    matplotlib.figure.Figure
        Figure that contains the plot.

    Raises
    ------
    TypeError
        If ``results``, ``fs``, or ``n_samples`` has the wrong type.
    ValueError
        If ``n_samples`` or ``fs`` is out of range, or a column is
        missing.
    """
    _check_results(results)
    _check_n_samples(n_samples)
    _check_sample_rate(fs)
    if n_samples > len(results):
        raise ValueError(
            f"n_samples must be at most {len(results)}, got {n_samples}"
        )
    _check_column(results, "dacp_value")
    _check_column(results, "dacn_value")
    if ax is None:
        figure, axis = plt.subplots(figsize=(10, 6))
    else:
        figure = ax.figure
        axis = ax
    time_seconds = np.arange(n_samples) / fs
    plotted = results.iloc[:n_samples]
    axis.plot(time_seconds, plotted["dacp_value"], label="DACP")
    axis.plot(time_seconds, plotted["dacn_value"], label="DACN")
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("DAC value")
    axis.set_title("DAC output")
    axis.legend()
    axis.grid()
    return figure


def plot_spectrum(
    results: pd.DataFrame,
    fs: float,
    osr: int | None = None,
    warmup_samples: int = 1000,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot the DACP spectrum after skipping warmup clocks.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`generate_dac_values`.
    fs : float
        Sample rate in hertz.
    osr : int or None, optional
        Draw the band edge at half the sample rate divided by this
        value. ``None`` draws no edge. Default is ``None``.
    warmup_samples : int, optional
        Leading clocks left out of the spectrum. Default is 1000.
    ax : matplotlib.axes.Axes or None, optional
        Axis to draw on. A new figure uses a logarithmic frequency
        axis.

    Returns
    -------
    matplotlib.figure.Figure
        Figure that contains the spectrum.

    Raises
    ------
    TypeError
        If an argument has the wrong type.
    ValueError
        If ``fs``, ``osr``, or ``warmup_samples`` is out of range.
    """
    _check_sample_rate(fs)
    if osr is not None:
        _check_osr(osr)
    spectrum = _calculate_dacp_spectrum(results, warmup_samples)
    n_fft = len(spectrum)
    full_scale = 128
    freq_bins = np.fft.fftfreq(n_fft, d=1 / fs)
    magnitude = np.abs(spectrum) * 2 / (full_scale * n_fft)
    with np.errstate(divide="ignore"):
        magnitude_db = 20 * np.log10(magnitude)
    positive = freq_bins >= 0
    if ax is None:
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.set_xscale("log")
    else:
        figure = ax.figure
        axis = ax
    axis.plot(freq_bins[positive], magnitude_db[positive], label="DACP")
    if osr is not None:
        cutoff_hz = (fs / 2) / osr
        cutoff_mhz = np.round(cutoff_hz / 1e6, 3)
        axis.axvline(
            x=cutoff_hz,
            color="r",
            linestyle="--",
            linewidth=1.5,
            label=f"$OSR={osr}$, $f_{{max}}={cutoff_mhz}$ MHz",
        )
    axis.set_xlabel("Frequency [Hz]")
    axis.set_ylabel("Magnitude [dBFS]")
    axis.set_title("DAC output spectrum")
    axis.legend()
    axis.grid(True, which="both", ls="-")
    return figure


class SineGenDACTests(unittest.TestCase):
    """Tests DAC generation, input checks, and in-band SQNR."""

    def _assert_rejects(
        self,
        error_type: type[BaseException],
        text: str,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Assert that generate_dac_values raises and names the input."""
        with self.assertRaises(error_type) as caught:
            generate_dac_values(*args, **kwargs)
        self.assertIn(text, str(caught.exception))

    def test_phase_follows_the_tuning_word(self) -> None:
        """Tests the 16-bit phase accumulator, including the high bit."""
        slow = generate_dac_values(4, frequency=1, dacp_mode="AC")
        np.testing.assert_array_equal(
            slow["phase"], np.array([0, 1, 2, 3], dtype=np.uint16)
        )
        fast = generate_dac_values(4, frequency=32768, dacp_mode="AC")
        half_turn = 1 << 15
        np.testing.assert_array_equal(
            fast["phase"],
            np.array([0, half_turn, 0, half_turn], dtype=np.uint16),
        )
        angles = FixedPointArray.from_mantissas(
            np.array([-half_turn], dtype=np.int64), 16, 16
        )
        expected = int(cordic_rotate(8, angles).get_mantissas()[0])
        self.assertEqual(int(fast["cosine"].iloc[1]), expected)
        wrapped = generate_dac_values(4, frequency=65535, dacp_mode="AC")
        np.testing.assert_array_equal(
            wrapped["phase"],
            np.array([0, 65535, 65534, 65533], dtype=np.uint16),
        )
        self._assert_rejects(ValueError, "got -1", 4, frequency=-1)
        self._assert_rejects(ValueError, "got 65536", 4, frequency=65536)
        self._assert_rejects(TypeError, "bool", 4, frequency=True)
        self._assert_rejects(TypeError, "float", 4, frequency=1.5)

    def test_defaults_match_scale_8_and_amplitude_15(self) -> None:
        """Tests the default scale, amplitude, and column order."""
        plain = generate_dac_values(
            8, frequency=1, dacp_mode="AC", dacn_mode="AC"
        )
        explicit = generate_dac_values(
            8,
            frequency=1,
            amplitude_scale=8,
            amplitude=15,
            dsm_enable=False,
            dacp_mode="AC",
            dacn_mode="AC",
            dacp_dc_value=0,
            dacn_dc_value=0,
            vdd=3.3,
        )
        pd.testing.assert_frame_equal(plain, explicit)
        self.assertEqual(
            list(plain.columns),
            [
                "phase",
                "cosine",
                "dacp_value",
                "dacn_value",
                "dacp_voltage",
                "dacn_voltage",
                "error",
            ],
        )

    def test_amplitude_shifts_the_cosine(self) -> None:
        """Tests a right shift by 15 minus the amplitude."""
        frame = generate_dac_values(
            4,
            frequency=16384,
            amplitude_scale=8,
            amplitude=15,
            dacp_mode="AC",
        )
        signed_phase = frame["phase"].to_numpy().astype(np.int16)
        angles = FixedPointArray.from_mantissas(
            signed_phase.astype(np.int64), 16, 16
        )
        cosine = cordic_rotate(8, angles)
        cos_integers = np.asarray(cosine.get_mantissas(), dtype=np.int64)
        np.testing.assert_array_equal(frame["cosine"], cos_integers)
        self.assertLess(int(cos_integers.min()), 0)
        shifted = generate_dac_values(
            4,
            frequency=16384,
            amplitude_scale=8,
            amplitude=14,
            dacp_mode="AC",
        )
        np.testing.assert_array_equal(shifted["cosine"], cos_integers >> 1)
        self._assert_rejects(ValueError, "got 16", 4, amplitude_scale=16)
        self._assert_rejects(ValueError, "got -1", 4, amplitude=-1)
        self._assert_rejects(
            TypeError, "uint8", 4, amplitude_scale=np.uint8(8)
        )
        self._assert_rejects(TypeError, "float", 4, amplitude=14.0)

    def test_full_scale_stays_inside_16_bits(self) -> None:
        """Tests that scale 15 and amplitude 15 stay inside 16 bits."""
        frame = generate_dac_values(
            8193,
            frequency=1,
            amplitude_scale=15,
            amplitude=15,
            dacp_mode="AC",
        )
        limit = (1 << 15) - 1
        self.assertLessEqual(int(frame["cosine"].max()), limit)
        self.assertGreaterEqual(int(frame["cosine"].min()), -limit - 1)
        angles = FixedPointArray.from_mantissas(
            np.array([8192], dtype=np.int64), 16, 16
        )
        direct = int(cordic_rotate(15, angles).get_mantissas()[0])
        self.assertEqual(int(frame["cosine"].iloc[8192]), direct)

    def test_dc_mode_holds_the_programmed_code(self) -> None:
        """Tests that DC mode replaces one channel and keeps the cosine."""
        frame = generate_dac_values(
            4,
            frequency=1,
            amplitude_scale=8,
            amplitude=15,
            dacp_mode="DC",
            dacn_mode="AC",
            dacp_dc_value=10,
            dacn_dc_value=20,
        )
        np.testing.assert_array_equal(frame["dacp_value"], np.full(4, 10))
        self.assertTrue(np.any(frame["dacn_value"].to_numpy() != 20))
        both = generate_dac_values(
            4,
            frequency=1,
            dacp_mode="DC",
            dacn_mode="DC",
            dacp_dc_value=3,
            dacn_dc_value=4,
        )
        np.testing.assert_array_equal(both["dacp_value"], np.full(4, 3))
        np.testing.assert_array_equal(both["dacn_value"], np.full(4, 4))
        self.assertGreater(int(np.ptp(both["cosine"])), 0)

    def test_voltages_follow_the_dac_code(self) -> None:
        """Tests that voltage is vdd times the code divided by 256."""
        frame = generate_dac_values(
            4,
            frequency=1,
            dacp_mode="AC",
            dacn_mode="AC",
            vdd=3.3,
        )
        np.testing.assert_allclose(
            frame["dacp_voltage"], frame["dacp_value"] * 3.3 / 256
        )
        np.testing.assert_allclose(
            frame["dacn_voltage"], frame["dacn_value"] * 3.3 / 256
        )

    def test_rejects_a_bad_sample_count(self) -> None:
        """Tests that n_samples names a bad type or value."""
        self._assert_rejects(TypeError, "bool", True)
        self._assert_rejects(TypeError, "float", 4.0)
        self._assert_rejects(ValueError, "got 0", 0)
        self._assert_rejects(ValueError, "got -3", -3)

    def test_rejects_a_bad_dac_mode(self) -> None:
        """Tests that each channel mode names the value it received."""
        self._assert_rejects(TypeError, "dacp", 4, dacp_mode=1)
        self._assert_rejects(ValueError, "got OFF", 4, dacp_mode="OFF")
        self._assert_rejects(TypeError, "dacn", 4, dacn_mode=None)
        self._assert_rejects(ValueError, "got OFF", 4, dacn_mode="OFF")

    def test_rejects_a_bad_dc_value(self) -> None:
        """Tests that each DC code names the value it received."""
        self._assert_rejects(TypeError, "dacp", 4, dacp_dc_value=True)
        self._assert_rejects(ValueError, "got 256", 4, dacp_dc_value=256)
        self._assert_rejects(TypeError, "dacn", 4, dacn_dc_value=1.0)
        self._assert_rejects(ValueError, "got -1", 4, dacn_dc_value=-1)

    def _quantized_sine_frame(self) -> pd.DataFrame:
        """Return a coherent 8-bit sine in the DACP column.

        The tone is bin 64 of 16384 samples. The peak integer is 127,
        so the quantizer does not clip. 128 is midscale.
        """
        n_samples = 2 ** 14
        tone_bin = 64
        amplitude = (1 << 7) - 1
        index = np.arange(n_samples)
        sine = amplitude * np.sin(
            2.0 * np.pi * tone_bin * index / n_samples
        )
        quantized = np.round(sine).astype(np.int64)
        return pd.DataFrame({"dacp_value": quantized + 128})

    def test_full_band_sqnr_matches_quantizer_formula(self) -> None:
        """Tests that an 8-bit coherent sine is near 6.02N + 1.76 dB."""
        frame = self._quantized_sine_frame()
        measured = calculate_sqnr_db(frame, osr=1, warmup_samples=0)
        expected = 6.02 * 8 + 1.76
        self.assertAlmostEqual(measured, expected, delta=1.0)

    def test_default_sqnr_is_the_signal_band(self) -> None:
        """Tests that the default OSR is 32."""
        frame = self._quantized_sine_frame()
        default = calculate_sqnr_db(frame, warmup_samples=0)
        named = calculate_sqnr_db(
            frame, osr=DEFAULT_OSR, warmup_samples=0
        )
        full_band = calculate_sqnr_db(frame, osr=1, warmup_samples=0)
        self.assertAlmostEqual(default, named)
        self.assertGreater(default, full_band)

    def test_in_band_sqnr_drops_the_out_of_band_noise(self) -> None:
        """Tests that a narrower band raises the SQNR of white noise."""
        frame = self._quantized_sine_frame()
        full_band = calculate_sqnr_db(frame, osr=1, warmup_samples=0)
        in_band = calculate_sqnr_db(frame, osr=16, warmup_samples=0)
        self.assertGreater(in_band, full_band + 10.0)
        self.assertLess(in_band, full_band + 18.0)

    def test_dc_offset_does_not_change_sqnr(self) -> None:
        """Tests that adding DC does not change the in-band SQNR."""
        frame = self._quantized_sine_frame()
        baseline = calculate_sqnr_db(frame, warmup_samples=0)
        shifted = frame.copy()
        shifted["dacp_value"] = shifted["dacp_value"] + 1000
        measured = calculate_sqnr_db(shifted, warmup_samples=0)
        self.assertAlmostEqual(measured, baseline, delta=0.5)

    def test_rejects_a_bad_osr_or_warmup(self) -> None:
        """Tests that OSR and warmup name the value they received."""
        frame = self._quantized_sine_frame()
        with self.assertRaises(ValueError) as caught:
            calculate_sqnr_db(frame, osr=0, warmup_samples=0)
        self.assertIn("got 0", str(caught.exception))
        with self.assertRaises(TypeError) as caught:
            calculate_sqnr_db(frame, osr=True, warmup_samples=0)
        self.assertIn("bool", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            calculate_sqnr_db(frame, warmup_samples=len(frame))
        self.assertIn(str(len(frame)), str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            calculate_sqnr_db(frame.iloc[:6], osr=1, warmup_samples=0)
        self.assertIn("got osr 1", str(caught.exception))

    def test_plot_functions_return_figures(self) -> None:
        """Tests that the plot helpers draw a short AC waveform."""
        frame = generate_dac_values(
            32, frequency=1, dacp_mode="AC", dacn_mode="AC"
        )
        output = plot_output(frame, 100e6, 16)
        spectrum = plot_spectrum(
            frame, 100e6, osr=2, warmup_samples=0
        )
        self.assertIsInstance(output, plt.Figure)
        self.assertIsInstance(spectrum, plt.Figure)
        plt.close("all")


def main() -> None:
    """Plot one DAC waveform with and without the delta-sigma modulator.

    Uses amplitude scale 8, amplitude 15, and tuning word 257.
    ``2**16`` samples after 1000 warmup clocks put the tone at FFT
    bin 257, inside the default OSR-32 band. The sample rate is 100 MHz.
    """
    n_samples = 2**16
    warmup_samples = 1000
    n_plot = 750
    fs = 100e6
    total = n_samples + warmup_samples
    print("Running DAC generation without DSM...")
    bypass = generate_dac_values(
        total,
        frequency=257,
        amplitude_scale=8,
        amplitude=15,
        dsm_enable=False,
        dacp_mode="AC",
        dacn_mode="AC",
    )
    figure, (time_axis, spectrum_axis) = plt.subplots(1, 2, figsize=(15, 6))
    settled = bypass.iloc[warmup_samples:]
    plot_output(settled, fs, n_plot, ax=time_axis)
    plot_spectrum(bypass, fs, warmup_samples=warmup_samples, ax=spectrum_axis)
    sqnr_no_dsm = calculate_sqnr_db(
        bypass, osr=DEFAULT_OSR, warmup_samples=warmup_samples
    )
    print(f"Bypass in-band SQNR {sqnr_no_dsm:.2f} dB (OSR {DEFAULT_OSR})")
    time_axis.lines[-2].set_label("DACP (No DSM)")
    time_axis.lines[-1].set_label("DACN (No DSM)")

    print("Running DAC generation with DSM...")
    modulated = generate_dac_values(
        total,
        frequency=257,
        amplitude_scale=8,
        amplitude=15,
        dsm_enable=True,
        dacp_mode="AC",
        dacn_mode="AC",
    )
    settled = modulated.iloc[warmup_samples:]
    plot_output(settled, fs, n_plot, ax=time_axis)
    plot_spectrum(
        modulated,
        fs,
        osr=DEFAULT_OSR,
        warmup_samples=warmup_samples,
        ax=spectrum_axis,
    )
    sqnr_dsm = calculate_sqnr_db(
        modulated, osr=DEFAULT_OSR, warmup_samples=warmup_samples
    )
    print(f"DSM in-band SQNR {sqnr_dsm:.2f} dB (OSR {DEFAULT_OSR})")
    time_axis.lines[-2].set_label("DACP (With DSM)")
    time_axis.lines[-1].set_label("DACN (With DSM)")
    spectrum_axis.lines[-3].set_label(
        f"In-band SQNR={np.round(sqnr_no_dsm, 1)} dB, no DSM"
    )
    spectrum_axis.lines[-2].set_label(
        f"In-band SQNR={np.round(sqnr_dsm, 1)} dB, with DSM"
    )
    time_axis.set_title(f"DAC output ({n_samples} cycles)")
    time_axis.legend()
    spectrum_axis.legend()
    time_axis.grid()
    spectrum_axis.grid()
    spectrum_axis.set_xscale("log")
    figure.tight_layout()
    figure.savefig("./dac_dsm_tseries.png")
    print("Test complete.")


if __name__ == "__main__":
    main()

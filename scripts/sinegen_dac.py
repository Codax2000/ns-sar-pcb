"""Differential sine-wave DAC model with an optional delta-sigma modulator.

The phase accumulator is unsigned 16-bit. The CORDIC vector format is
signed ``(16, 15)``. The DAC quantizer is signed 8-bit, then stored as
an unsigned code. ``convert`` returns integer codes. ``get_sqnr_db``
defaults to the signal band at OSR 32.
"""

from __future__ import annotations

import math
import unittest
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numba import njit

from cordic import CORDIC, PHASE_BITS


# Reset value of AC_CONFIG.amplitude. 15 means no right shift.
FULL_SCALE_EXPONENT = 15
# Reset value of AC_CONFIG.amplitude_scale. Weight is 8/16.
DEFAULT_AMPLITUDE_SCALE = 8
# Blackman main lobe: the peak bin and three bins on either side.
BLACKMAN_HALF_WIDTH = 3
# Default signal band for get_sqnr_db. Same OSR as scripts/nssar.py.
DEFAULT_OSR = 32


def _signed_limits(width: int) -> tuple[int, int]:
    """Return the inclusive range of a signed word.

    Parameters
    ----------
    width : int
        Bit width, including the sign bit.

    Returns
    -------
    tuple of int
        ``(-(2**(width - 1)), 2**(width - 1) - 1)``.
    """
    half = 1 << (width - 1)
    return -half, half - 1


def _saturate(values: np.ndarray, width: int) -> np.ndarray:
    """Saturate integer ``values`` to a signed word.

    Parameters
    ----------
    values : numpy.ndarray
        Integer codes.
    width : int
        Signed width, including the sign bit.

    Returns
    -------
    numpy.ndarray
        ``int64`` codes clipped to the signed range.
    """
    low, high = _signed_limits(width)
    return np.clip(values, low, high).astype(np.int64)


@njit
def _run_dsm_loop(
    samples: np.ndarray,
    shift: int,
    low: int,
    high: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Run a second-order delta-sigma quantizer on integer samples.

    Parameters
    ----------
    samples : numpy.ndarray
        ``int64`` CORDIC codes.
    shift : int
        Bits dropped by the quantizer. The shift is arithmetic.
    low : int
        Smallest signed DAC code.
    high : int
        Largest signed DAC code.

    Returns
    -------
    tuple of numpy.ndarray
        Saturated DAC codes and the feedback error, both ``int64``.
    """
    count = samples.shape[0]
    codes = np.empty(count, dtype=np.int64)
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
            code = high
        elif truncated < low:
            code = low
        else:
            code = truncated
        codes[index] = code
        # Opposite sign from the bypass error in _quantize.
        error[index] = (code << shift) - accumulator
    return codes, error


class SineGenDAC:
    """Model a differential AC/DC sine generator and its DAC.

    AC mode drives the DAC from the fixed-point CORDIC. DC mode holds
    the programmed code. The two DAC channels can be set independently.
    """

    def __init__(
        self,
        n_dac_bits: int = 8,
        n_cordic_bits: int = 16,
        fs: float = 100e6,
        vdd: float = 3.3,
    ) -> None:
        """Set the word widths, sample rate, and default registers.

        Parameters
        ----------
        n_dac_bits : int, optional
            Signed DAC width before the unsigned offset. Default is 8.
            Must be at least 1 and no wider than the CORDIC.
        n_cordic_bits : int, optional
            CORDIC width and iteration count. Default is 16. Fractional
            bits are ``n_cordic_bits - 1``.
        fs : float, optional
            Sample rate in hertz. Default is 100 MHz.
        vdd : float, optional
            DAC supply in volts. ``convert`` returns codes. Default
            is 3.3.

        Raises
        ------
        ValueError
            If a width cannot represent the CORDIC or DAC formats.
        """
        if n_cordic_bits < 2 or n_dac_bits < 1:
            raise ValueError("CORDIC width must be >= 2 and DAC width >= 1")
        if n_dac_bits > n_cordic_bits:
            raise ValueError("DAC width cannot exceed the CORDIC width")
        self._reg: dict[str, Any] = {
            "frequency": 0x0,
            "amplitude_scale": DEFAULT_AMPLITUDE_SCALE,
            "amplitude": FULL_SCALE_EXPONENT,
            "dacp_mode": "DC",
            "dacn_mode": "DC",
            "dsm_enable": False,
            "dacp_dc_value": 0x0,
            "dacn_dc_value": 0x0,
            "warmup_cycles": 1000,
            "osr": DEFAULT_OSR,
        }
        self._n_dac_bits: int = n_dac_bits
        self._n_cordic_bits: int = n_cordic_bits
        self._vector_fraction: int = n_cordic_bits - 1
        self._fs: float = fs
        self._vdd: float = vdd
        self._cordic: CORDIC = CORDIC(
            n_rotations=n_cordic_bits,
            n_x=n_cordic_bits,
            r_x=self._vector_fraction,
        )
        self._time_seconds: np.ndarray = np.zeros(0, dtype=float)
        self._phase: np.ndarray = np.zeros(0, dtype=np.uint16)
        self._sin: np.ndarray = np.zeros(0, dtype=np.int64)
        self._cos: np.ndarray = np.zeros(0, dtype=np.int64)
        self._quant: np.ndarray = np.zeros(0, dtype=np.int64)
        self._quant_bar: np.ndarray = np.zeros(0, dtype=np.int64)
        self._error: np.ndarray = np.zeros(0, dtype=np.int64)
        self._results: pd.DataFrame | None = None
        self._fft_data: np.ndarray | None = None

    def set_frequency(self, frequency: int) -> None:
        """Store the 16-bit frequency tuning word.

        Parameters
        ----------
        frequency : int
            Tuning word from 0 to 65535. The phase accumulator adds
            this word modulo ``2**16``. ``f_out = frequency * fs /
            2**16``.

        Raises
        ------
        ValueError
            If ``frequency`` is outside 0 to 65535.
        """
        if frequency < 0 or frequency > 2**16 - 1:
            raise ValueError("Frequency must be between 0 and 65535")
        self._reg["frequency"] = frequency

    def set_amplitude_scale(self, scale: int) -> None:
        """Store ``AC_CONFIG.amplitude_scale``.

        Parameters
        ----------
        scale : int
            Unsigned code from 0 to 15. Weight is ``scale / 16`` of
            the amplitude set by :meth:`set_amplitude`.

        Raises
        ------
        ValueError
            If ``scale`` is outside 0 to 15.
        """
        if scale < 0 or scale > 2**4 - 1:
            raise ValueError("Amplitude scale must be between 0 and 15")
        self._reg["amplitude_scale"] = scale

    def set_amplitude(self, amplitude: int) -> None:
        """Store ``AC_CONFIG.amplitude``.

        Parameters
        ----------
        amplitude : int
            Code from 0 to 15. The CORDIC output is shifted right by
            ``15 - amplitude``. Code 15 leaves the codes unchanged.

        Raises
        ------
        ValueError
            If ``amplitude`` is outside 0 to 15.
        """
        if amplitude < 0 or amplitude > 2**4 - 1:
            raise ValueError("Amplitude exponent must be between 0 and 15")
        self._reg["amplitude"] = amplitude

    def set_dac_mode(self, dac_number: int = 0, mode: str = "DC") -> None:
        """Select AC or DC for one DAC channel.

        Parameters
        ----------
        dac_number : int, optional
            ``0`` for DACP and ``1`` for DACN. Default is 0.
        mode : str, optional
            ``"DC"`` or ``"AC"``. Default is ``"DC"``.

        Raises
        ------
        ValueError
            If the channel or mode is not recognized.
        """
        if mode not in ("DC", "AC"):
            raise ValueError("DAC mode must be either DC or AC")
        if dac_number not in (0, 1):
            raise ValueError("DAC number must be 0 or 1")
        if dac_number == 0:
            self._reg["dacp_mode"] = mode
        else:
            self._reg["dacn_mode"] = mode

    def set_dsm_enable(self, enable: bool = True) -> None:
        """Enable or disable the delta-sigma modulator.

        Parameters
        ----------
        enable : bool, optional
            True runs the error-feedback quantizer. False truncates by
            a shift. Default is True.
        """
        self._reg["dsm_enable"] = enable

    def set_osr(self, osr: int) -> None:
        """Store the oversampling ratio of the signal band.

        Parameters
        ----------
        osr : int
            Positive integer. The band edge is ``fs / (2 * osr)``.
            :meth:`get_sqnr_db` uses this value when no OSR is passed.
            :meth:`plot_output_fft` draws that edge when asked. The
            default is :data:`DEFAULT_OSR`.

        Raises
        ------
        ValueError
            If ``osr`` is less than 1.
        """
        if osr < 1:
            raise ValueError("OSR must be a positive integer")
        self._reg["osr"] = osr

    def _phase_step(self) -> int:
        """Return the tuning word, which is the phase step.

        Returns
        -------
        int
            Step added by the phase accumulator, modulo ``2**16``.
        """
        return self._reg["frequency"]

    def _exponent_shift(self) -> int:
        """Return how many bits to shift the CORDIC output right.

        Returns
        -------
        int
            ``15 - amplitude``. The shift is arithmetic, toward
            negative infinity. Zero when amplitude is 15.
        """
        return FULL_SCALE_EXPONENT - self._reg["amplitude"]

    def _calculate_phase(self, n_samples: int) -> None:
        """Fill the phase accumulator for ``n_samples`` clocks.

        Parameters
        ----------
        n_samples : int
            Number of clocks, including warmup.
        """
        step = np.uint64(self._phase_step())
        modulus = np.uint64(1 << PHASE_BITS)
        sample_index = np.arange(n_samples, dtype=np.uint64)
        # phase[k] = (k * step) mod 2**16, starting from 0.
        self._phase = ((sample_index * step) % modulus).astype(np.uint16)

    def _calculate_cordic(self) -> None:
        """Fill sine and cosine codes for the current phase.

        The vector format is ``(n_cordic_bits, n_cordic_bits - 1)``.
        The initial magnitude comes from ``amplitude_scale``.
        """
        cosine, sine = self._cordic.rotate_preload(
            self._reg["amplitude_scale"], self._phase
        )
        shift = self._exponent_shift()
        # Arithmetic right shift. Truncates toward negative infinity.
        self._cos = np.asarray(cosine.values, dtype=np.int64) >> shift
        self._sin = np.asarray(sine.values, dtype=np.int64) >> shift

    def _quantize(self) -> None:
        """Quantize cosine to the signed DAC width and record the error.

        Without the modulator, the code is an arithmetic right shift
        by ``n_cordic_bits - n_dac_bits``, then saturated. The stored
        error is ``cosine - (code << shift)``. With the modulator,
        :func:`_run_dsm_loop` does that quantizer. DACN is the
        saturated negation of the DACP code.
        """
        shift = self._n_cordic_bits - self._n_dac_bits
        low, high = _signed_limits(self._n_dac_bits)
        if self._reg["dsm_enable"]:
            self._quant, self._error = _run_dsm_loop(
                self._cos, shift, low, high
            )
        else:
            truncated = self._cos >> shift
            self._quant = _saturate(truncated, self._n_dac_bits)
            self._error = self._cos - (self._quant << shift)
        self._quant_bar = _saturate(-self._quant, self._n_dac_bits)

    def convert(self, n_samples: int) -> pd.DataFrame:
        """Run ``n_samples`` conversions and return the waveform table.

        Warmup cycles from the register map are prepended. DAC outputs
        in AC mode are unsigned codes: the signed quantizer word plus
        ``2**(n_dac_bits - 1)``. DC mode uses the programmed DC code.

        Parameters
        ----------
        n_samples : int
            Number of samples after warmup.

        Returns
        -------
        pandas.DataFrame
            Columns ``time_seconds``, ``phase``, ``cordic_sin``,
            ``cordic_cos``, ``dacp_output``, ``dacn_output``, and
            ``error``. A copy is returned.
        """
        total = n_samples + self._reg["warmup_cycles"]
        self._time_seconds = np.arange(total) / self._fs
        self._calculate_phase(total)
        self._calculate_cordic()
        self._quantize()
        offset = 1 << (self._n_dac_bits - 1)
        dacp_ac = self._quant + offset
        dacn_ac = self._quant_bar + offset
        has_ac_mode = (
            self._reg["dacp_mode"] == "AC" or self._reg["dacn_mode"] == "AC"
        )
        if self._reg["dacp_mode"] == "AC":
            dacp_output = dacp_ac
        else:
            dacp_output = self._reg["dacp_dc_value"]
        if self._reg["dacn_mode"] == "AC":
            dacn_output = dacn_ac
        else:
            dacn_output = self._reg["dacn_dc_value"]
        self._results = pd.DataFrame({
            "time_seconds": self._time_seconds,
            "phase": self._phase if has_ac_mode else 0,
            "cordic_sin": self._sin if has_ac_mode else 0,
            "cordic_cos": self._cos if has_ac_mode else 0,
            "dacp_output": dacp_output,
            "dacn_output": dacn_output,
            "error": self._error if has_ac_mode else 0,
        })
        return self._results.copy()

    def plot_output(
        self,
        n_samples: int,
        ax: plt.Axes | None = None,
    ) -> plt.Figure:
        """Plot DACP and DACN over ``n_samples`` after warmup.

        Parameters
        ----------
        n_samples : int
            Number of samples to plot after the warmup cycles.
        ax : matplotlib.axes.Axes, optional
            Axis to draw on. A new figure is created when omitted.

        Returns
        -------
        matplotlib.figure.Figure
            Figure that contains the plot.

        Raises
        ------
        ValueError
            If :meth:`convert` has not been called.
        """
        if self._results is None:
            raise ValueError(
                "Must run conversion before plotting is attempted"
            )
        total_samples = n_samples + self._reg["warmup_cycles"]
        warmup = self._reg["warmup_cycles"]
        plot_data = self._results.iloc[warmup:total_samples]
        if ax is None:
            figure, axis = plt.subplots(figsize=(10, 6))
        else:
            figure = ax.figure
            axis = ax
        axis.plot(
            plot_data["time_seconds"],
            plot_data["dacp_output"],
            label="DACP Output",
        )
        axis.plot(
            plot_data["time_seconds"],
            plot_data["dacn_output"],
            label="DACN Output",
        )
        axis.set_xlabel("Time (s)")
        axis.set_ylabel("DAC Output Value")
        axis.set_title("Sine Wave Generator DAC Output")
        axis.legend()
        axis.grid()
        return figure

    def plot_output_fft(
        self,
        ax: plt.Axes | None = None,
        add_osrline: bool = False,
    ) -> plt.Figure:
        """Plot the DACP spectrum after warmup.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axis to draw on. A new figure uses a logarithmic frequency
            axis.
        add_osrline : bool, optional
            Draw a vertical line at ``fs / (2 * osr)``. Default is False.

        Returns
        -------
        matplotlib.figure.Figure
            Figure that contains the spectrum.

        Raises
        ------
        ValueError
            If :meth:`convert` has not been called.
        """
        if self._results is None:
            raise ValueError(
                "Must run conversion before plotting is attempted"
            )
        warmup = self._reg["warmup_cycles"]
        n_samples_for_fft = len(self._results) - warmup
        data_for_fft = self._results.iloc[warmup:]
        # Unsigned midscale is 2**(n-1).
        full_scale = 2 ** (self._n_dac_bits - 1)
        dc_offset = float(full_scale)
        dacp_no_dc = data_for_fft["dacp_output"] - dc_offset
        window = np.blackman(n_samples_for_fft)
        windowed_dacp = dacp_no_dc * window
        fft_output_dacp = np.fft.fft(windowed_dacp)
        self._fft_data = fft_output_dacp
        freq_bins = np.fft.fftfreq(n_samples_for_fft, d=1 / self._fs)
        magnitude = np.abs(fft_output_dacp) * 2
        magnitude = magnitude / (full_scale * n_samples_for_fft)
        fft_magnitude_db = 20 * np.log10(magnitude)
        positive_freq = freq_bins >= 0
        freq_bins = freq_bins[positive_freq]
        fft_magnitude_db = fft_magnitude_db[positive_freq]
        if ax is None:
            figure, axis = plt.subplots(figsize=(10, 6))
            axis.set_xscale("log")
        else:
            figure = ax.figure
            axis = ax
        axis.plot(freq_bins, fft_magnitude_db, label="DACP FFT")
        if add_osrline:
            osr = self._reg["osr"]
            cutoff_hz = (self._fs / 2) / osr
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
        axis.set_title("Sine Wave Generator DAC Output FFT")
        axis.legend()
        axis.grid(True, which="both", ls="-")
        return figure

    def _band_last_bin(self, count: int, osr: int) -> int:
        """Return the last FFT bin included in the noise sum.

        Parameters
        ----------
        count : int
            Length of the FFT, which is the number of time samples.
        osr : int
            Oversampling ratio. The last bin is the one at
            ``fs / (2 * osr)``. ``1`` keeps every bin through Nyquist.

        Returns
        -------
        int
            Inclusive last bin index.

        Raises
        ------
        ValueError
            If ``osr`` is less than 1, or the band does not clear the
            DC leakage bins.
        """
        nyquist = count // 2
        if isinstance(osr, bool) or not isinstance(osr, int) or osr < 1:
            raise ValueError("OSR must be a positive integer")
        last = count // (2 * osr)
        if last <= BLACKMAN_HALF_WIDTH:
            raise ValueError("band does not clear the DC leakage bins")
        return min(last, nyquist)

    def get_sqnr_db(self, osr: int | None = None) -> float:
        """Return the signal-to-quantization-noise ratio in decibels.

        Uses the windowed FFT from :meth:`plot_output_fft`. The tone is
        the strongest bin above DC. Signal power is that bin and three
        bins on either side, the Blackman main lobe. Noise is the other
        bins from bin 4 through the signal band. Bins 0 to 3 are left
        out.

        Parameters
        ----------
        osr : int or None, optional
            Band edge is ``fs / (2 * osr)``. ``None`` uses the OSR
            register (:data:`DEFAULT_OSR`). ``1`` is the Nyquist band.

        Returns
        -------
        float
            SQNR in dB, or infinity when the noise power is zero.

        Raises
        ------
        ValueError
            If the FFT is missing, ``osr`` is invalid, or the band has
            no bins above DC.
        """
        if self._fft_data is None:
            raise ValueError(
                "plot_output_fft must be run first to populate FFT data."
            )
        if osr is None:
            osr = self._reg["osr"]
        fft_data = self._fft_data
        count = len(fft_data)
        last_bin = self._band_last_bin(count, osr)
        power = np.abs(fft_data) ** 2
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

    def get_filtered_output(self) -> None:
        """Return the waveform after the board reconstruction filter.

        Returns
        -------
        None
            The reconstruction filter is not modeled.
        """
        return None


class SineGenDACTests(unittest.TestCase):
    """Tests the tuning word and the amplitude registers."""

    def _converter(self) -> SineGenDAC:
        """Return a DAC with no warmup and DACP in AC mode.

        Returns
        -------
        SineGenDAC
            Converter ready for a short ``convert`` call.
        """
        dac = SineGenDAC()
        dac.set_dac_mode(dac_number=0, mode="AC")
        dac._reg["warmup_cycles"] = 0
        return dac

    def test_tuning_word_is_the_frequency_register(self) -> None:
        """Tests that the phase step is the 16-bit tuning word."""
        dac = self._converter()
        for word in (0, 1, 257, 32768, 65535):
            dac.set_frequency(word)
            self.assertEqual(dac._phase_step(), word)
        dac.set_frequency(1)
        slow = dac.convert(4)
        np.testing.assert_array_equal(
            slow["phase"], np.array([0, 1, 2, 3], dtype=np.uint16)
        )
        dac.set_frequency(32768)
        fast = dac.convert(4)
        half_turn = 1 << (PHASE_BITS - 1)
        np.testing.assert_array_equal(
            fast["phase"],
            np.array([0, half_turn, 0, half_turn], dtype=np.uint16),
        )
        dac.set_frequency(65535)
        wrapped = dac.convert(4)
        np.testing.assert_array_equal(
            wrapped["phase"],
            np.array([0, 65535, 65534, 65533], dtype=np.uint16),
        )
        with self.assertRaises(ValueError):
            dac.set_frequency(-1)
        with self.assertRaises(ValueError):
            dac.set_frequency(65536)

    def test_reset_amplitude_is_scale_8_exponent_15(self) -> None:
        """Tests the reset values of the amplitude registers."""
        dac = SineGenDAC()
        self.assertEqual(dac._reg["amplitude_scale"], DEFAULT_AMPLITUDE_SCALE)
        self.assertEqual(dac._reg["amplitude"], FULL_SCALE_EXPONENT)

    def test_exponent_shifts_the_preloaded_cordic(self) -> None:
        """Tests the scale and a right shift by ``15 - amplitude``."""
        dac = self._converter()
        dac.set_amplitude_scale(8)
        dac.set_amplitude(FULL_SCALE_EXPONENT)
        dac.set_frequency(16384)
        frame = dac.convert(4)
        cosine, sine = dac._cordic.rotate_preload(
            8, frame["phase"].to_numpy()
        )
        cos_codes = np.asarray(cosine.values, dtype=np.int64)
        sin_codes = np.asarray(sine.values, dtype=np.int64)
        np.testing.assert_array_equal(frame["cordic_cos"], cos_codes)
        np.testing.assert_array_equal(frame["cordic_sin"], sin_codes)
        self.assertLess(int(cos_codes.min()), 0)
        dac.set_amplitude(14)
        shifted = dac.convert(4)
        np.testing.assert_array_equal(shifted["cordic_cos"], cos_codes >> 1)
        np.testing.assert_array_equal(shifted["cordic_sin"], sin_codes >> 1)
        with self.assertRaises(ValueError):
            dac.set_amplitude_scale(16)
        with self.assertRaises(ValueError):
            dac.set_amplitude(-1)

    def test_full_scale_preload_stays_in_the_cordic_word(self) -> None:
        """Tests that scale 15 and amplitude 15 stay inside 16 bits."""
        dac = self._converter()
        dac.set_amplitude_scale(15)
        dac.set_amplitude(FULL_SCALE_EXPONENT)
        dac.set_frequency(1)
        # Phase equals the sample index, so index 8192 is pi/4.
        frame = dac.convert(8193)
        quarter = frame.iloc[8192]
        preload = dac._cordic.preload(15)
        radius = preload * dac._cordic.gain
        expected = radius * math.sqrt(2.0) / 2.0
        self.assertAlmostEqual(
            float(quarter["cordic_cos"]), expected, delta=20
        )
        self.assertAlmostEqual(
            float(quarter["cordic_sin"]), expected, delta=20
        )
        limit = (1 << (dac._n_cordic_bits - 1)) - 1
        self.assertLessEqual(int(frame["cordic_cos"].max()), limit)
        self.assertGreaterEqual(int(frame["cordic_cos"].min()), -limit - 1)
        direct_cos, direct_sin = dac._cordic.rotate_preload(
            15, np.array([8192])
        )
        self.assertEqual(
            int(quarter["cordic_cos"]), int(direct_cos.values[0])
        )
        self.assertEqual(int(quarter["cordic_sin"]), int(direct_sin.values[0]))

    def _quantized_sine_spectrum(self) -> np.ndarray:
        """Return the Blackman FFT of a coherent 8-bit sine.

        Returns
        -------
        numpy.ndarray
            Complex spectrum. The tone is bin 64 of 16384 samples, with
            peak code 127 so the quantizer does not clip.
        """
        n_bits = 8
        n_samples = 2 ** 14
        tone_bin = 64
        amplitude = (1 << (n_bits - 1)) - 1
        index = np.arange(n_samples)
        sine = amplitude * np.sin(
            2.0 * np.pi * tone_bin * index / n_samples
        )
        codes = np.round(sine)
        return np.fft.fft(codes * np.blackman(n_samples))

    def test_full_band_sqnr_matches_quantizer_formula(self) -> None:
        """Tests that an 8-bit coherent sine is near 6.02N + 1.76 dB."""
        dac = self._converter()
        dac._fft_data = self._quantized_sine_spectrum()
        measured = dac.get_sqnr_db(osr=1)
        expected = 6.02 * 8 + 1.76
        self.assertAlmostEqual(measured, expected, delta=1.0)

    def test_default_sqnr_is_the_signal_band(self) -> None:
        """Tests that the default SQNR uses the OSR register."""
        dac = self._converter()
        dac._fft_data = self._quantized_sine_spectrum()
        self.assertEqual(dac._reg["osr"], DEFAULT_OSR)
        default = dac.get_sqnr_db()
        self.assertAlmostEqual(default, dac.get_sqnr_db(osr=DEFAULT_OSR))
        self.assertGreater(default, dac.get_sqnr_db(osr=1))

    def test_in_band_sqnr_drops_the_out_of_band_noise(self) -> None:
        """Tests that a narrower band raises the SQNR of white noise."""
        dac = self._converter()
        dac._fft_data = self._quantized_sine_spectrum()
        full_band = dac.get_sqnr_db(osr=1)
        in_band = dac.get_sqnr_db(osr=16)
        # A white spectrum gains about 12 dB when the band shrinks by 16.
        self.assertGreater(in_band, full_band + 10.0)
        self.assertLess(in_band, full_band + 18.0)

    def test_dc_offset_is_not_scored_as_the_tone(self) -> None:
        """Tests that adding DC does not change the in-band SQNR."""
        dac = self._converter()
        spectrum = self._quantized_sine_spectrum()
        dac._fft_data = spectrum
        baseline = dac.get_sqnr_db()
        n_samples = len(spectrum)
        dc_term = 1000.0 * np.blackman(n_samples)
        dac._fft_data = spectrum + np.fft.fft(dc_term)
        self.assertAlmostEqual(dac.get_sqnr_db(), baseline, delta=0.5)
        with self.assertRaises(ValueError):
            dac.get_sqnr_db(osr=0)


def main() -> None:
    """Plot one DAC waveform with and without the delta-sigma modulator.

    Uses amplitude scale 8, amplitude 15, and tuning word 257.
    ``2**16`` samples put the tone at FFT bin 257, inside the default
    OSR-32 band.
    """
    print("Running SineGenDAC test without DSM...")
    dac = SineGenDAC()
    dac.set_frequency(257)
    dac.set_amplitude_scale(DEFAULT_AMPLITUDE_SCALE)
    dac.set_amplitude(FULL_SCALE_EXPONENT)
    dac.set_osr(DEFAULT_OSR)
    dac.set_dac_mode(dac_number=0, mode="AC")
    dac.set_dac_mode(dac_number=1, mode="AC")

    n_cycles = 2**16
    n_plot_cycles = 750
    dac.convert(n_cycles)

    figure, (time_axis, spectrum_axis) = plt.subplots(1, 2, figsize=(15, 6))
    dac.plot_output(n_plot_cycles, ax=time_axis)
    dac.plot_output_fft(ax=spectrum_axis)
    demo_osr = dac._reg["osr"]
    sqnr_no_dsm = dac.get_sqnr_db()
    print(f"Bypass in-band SQNR {sqnr_no_dsm:.2f} dB (OSR {demo_osr})")
    time_axis.lines[-2].set_label("DACP Output (No DSM)")
    time_axis.lines[-1].set_label("DACN Output (No DSM)")

    print("Running SineGenDAC test with DSM...")
    dac.set_dsm_enable(enable=True)
    dac.convert(n_cycles)

    dac.plot_output(n_plot_cycles, ax=time_axis)
    dac.plot_output_fft(ax=spectrum_axis, add_osrline=True)
    sqnr_dsm = dac.get_sqnr_db()
    print(f"DSM in-band SQNR {sqnr_dsm:.2f} dB (OSR {demo_osr})")
    time_axis.lines[-2].set_label("DACP Output (With DSM)")
    time_axis.lines[-1].set_label("DACN Output (With DSM)")

    spectrum_axis.lines[-3].set_label(
        f"In-band SQNR={np.round(sqnr_no_dsm, 1)} dB, no DSM"
    )
    spectrum_axis.lines[-2].set_label(
        f"In-band SQNR={np.round(sqnr_dsm, 1)} dB, with DSM"
    )

    time_axis.set_title(f"Sine Wave Generator DAC Output ({n_cycles} cycles)")
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

"""Differential sine-wave DAC model with an optional delta-sigma modulator.

The datapath is an integer phase accumulator, a fixed-point CORDIC, a
truncating DAC quantizer, and an optional second-order error-feedback
modulator. Widths below are the defaults (16-bit CORDIC, 8-bit DAC):

* Phase accumulator: unsigned 16-bit word. ``2**16`` codes is one turn.
  The frequency register selects ``step = 1 << frequency``. Codes 0 to
  15 are valid. Code 15 steps by half a turn (``2**15``), so the
  accumulator alternates between 0 and ``2**15``.
* Amplitude register: code ``a`` sets the CORDIC initial-vector length
  to ``2**(a - 15)``. Code 15 is full scale. ``AC_CONFIG.amplitude`` is
  a power of two and calls ``4'hF`` full scale; this is that reading.
* CORDIC vector: signed ``(16, 15)``. Outputs are that magnitude times
  cosine and sine, in units of ``2**(-15)``. ``+1`` saturates because
  it is not a signed code. ``1/K`` is applied inside the CORDIC.
* CORDIC angle: the phase code itself, a U0.16 fraction of a turn.
* DAC quantizer: arithmetic right shift by 8, then saturate to signed
  8-bit. Adding ``2**7`` makes the unsigned DAC code.
* Delta-sigma modulator: the same shift and saturation, with the
  quantization error fed back in CORDIC mantissa units.

``convert`` returns integer codes, not volts.
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


# 4'hF is full scale in dac_registers.rdl. Code ``a`` has magnitude
# 2**(a - FULL_SCALE_AMPLITUDE).
FULL_SCALE_AMPLITUDE = 15


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
    """Run a second-order error-feedback quantizer on integer samples.

    The state is integer because ``samples``, the right-shift quantizer,
    and the error are all CORDIC mantissa units. Numba only compiles the
    sample loop. The quantizer is an arithmetic right shift followed by
    saturation to ``[low, high]``. The error fed back is
    ``(code << shift) - accumulator``, so a clipped code is visible to
    the loop. That error uses the opposite sign from the bypass path in
    :meth:`SineGenDAC.convert`, which stores
    ``input - (code << shift)``.

    Parameters
    ----------
    samples : numpy.ndarray
        ``int64`` CORDIC mantissas.
    shift : int
        Bits dropped by the DAC quantizer.
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
            Signed DAC quantizer width before the unsigned offset.
            Default is 8. Must be at least 1 and no wider than the
            CORDIC.
        n_cordic_bits : int, optional
            CORDIC vector width and iteration count. Default is 16.
            The vector fraction is ``n_cordic_bits - 1``. The angle is
            the 16-bit phase code, not a separate radian format.
        fs : float, optional
            Sample rate in hertz. Default is 100 MHz.
        vdd : float, optional
            Supply used to describe the DAC. ``convert`` returns codes,
            not volts. Default is 3.3.

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
            "amplitude": 0xF,
            "dacp_mode": "DC",
            "dacn_mode": "DC",
            "dsm_enable": False,
            "dacp_dc_value": 0x0,
            "dacn_dc_value": 0x0,
            "warmup_cycles": 1000,
            "osr": 8,
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
        """Store the 4-bit frequency code.

        Parameters
        ----------
        frequency : int
            Code from 0 to 15. The phase step is ``1 << frequency``, so
            each increment doubles the step. Code 15 steps by half a
            turn per sample.

        Raises
        ------
        ValueError
            If ``frequency`` is outside 0 to 15.
        """
        if frequency < 0 or frequency > 2**4 - 1:
            raise ValueError("Frequency must be between 0 and 15")
        self._reg["frequency"] = frequency

    def set_amplitude(self, amplitude: int) -> None:
        """Store the 4-bit amplitude code.

        Parameters
        ----------
        amplitude : int
            Code from 0 to 15. The CORDIC initial vector has length
            ``2**(amplitude - 15)``. Code 15 is full scale, and each
            decrease halves that length.

        Raises
        ------
        ValueError
            If ``amplitude`` is outside 0 to 15.
        """
        if amplitude < 0 or amplitude > 2**4 - 1:
            raise ValueError("Amplitude must be between 0 and 15")
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
        """Store the oversampling ratio used by the spectrum helpers.

        Parameters
        ----------
        osr : int
            Positive integer. The noise band in :meth:`get_sqnr_db` and
            the FFT marker use ``fs / (2 * osr)``.

        Raises
        ------
        ValueError
            If ``osr`` is less than 1.
        """
        if osr < 1:
            raise ValueError("OSR must be a positive integer")
        self._reg["osr"] = osr

    def _phase_step(self) -> int:
        """Return the phase increment for the frequency register.

        The tuning word is ``1 << frequency``. Valid codes are 0 through
        15, so the step is 1, 2, 4, ..., ``2**15``. Code 15 is half a
        turn per sample: the accumulator alternates between 0 and
        ``2**15``. Every in-range step fits in the 16-bit phase word.
        The accumulator adds this step modulo ``2**16``.

        Returns
        -------
        int
            Phase step in U0.16 codes.
        """
        return 1 << self._reg["frequency"]

    def _vector_magnitude(self) -> float:
        """Return the CORDIC initial-vector length for the amplitude.

        ``AC_CONFIG.amplitude`` is a power of two, and code ``4'hF`` is
        full scale. Code ``a`` therefore has length ``2**(a - 15)``:
        15 is 1, 14 is 1/2, and 0 is ``2**(-15)``. The CORDIC quantizes
        that length into the vector format, so full scale saturates
        where ``+1`` is not a signed code.

        Returns
        -------
        float
            Initial x component. The initial y component is 0.
        """
        code = self._reg["amplitude"]
        return 2.0 ** (code - FULL_SCALE_AMPLITUDE)

    def _calculate_phase(self, n_samples: int) -> None:
        """Fill the phase accumulator for ``n_samples`` clocks.

        The hardware recurrence is ``phase <= (phase + step) mod 2**16``
        with ``phase`` starting at 0. Sample ``k`` therefore holds
        ``(k * step) mod 2**16``.

        Parameters
        ----------
        n_samples : int
            Number of accumulator clocks, including warmup.
        """
        step = np.uint64(self._phase_step())
        modulus = np.uint64(1 << PHASE_BITS)
        sample_index = np.arange(n_samples, dtype=np.uint64)
        self._phase = ((sample_index * step) % modulus).astype(np.uint16)

    def _calculate_cordic(self) -> None:
        """Fill sine and cosine mantissas for the current phase.

        The initial vector is ``(amplitude_magnitude, 0)``, so the
        quadrant pre-rotation and the ``1/K`` scale both see the
        programmed amplitude. The vector format is
        ``(n_cordic_bits, n_cordic_bits - 1)``. Results are saturated
        signed codes in that format.
        """
        magnitude = self._vector_magnitude()
        cosine, sine = self._cordic.rotate(magnitude, 0, self._phase)
        self._cos = cosine.values.astype(np.int64)
        self._sin = sine.values.astype(np.int64)

    def _quantize(self) -> None:
        """Quantize cosine to the signed DAC width and record the error.

        Bypass mode shifts the CORDIC mantissa right by
        ``n_cordic_bits - n_dac_bits`` and saturates. The stored error is
        ``cosine - (code << shift)``. DSM mode uses
        :func:`_run_dsm_loop`. DACN is the saturated negation of the
        signed DACP code.
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
        full_scale = 2 ** (self._n_dac_bits - 1)
        dc_offset = full_scale / 2.0
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

    def get_sqnr_db(self) -> float:
        """Return the signal-to-quantization-noise ratio in decibels.

        The signal is the peak FFT bin plus two bins on either side.
        Noise is the remaining positive-frequency power inside the
        oversampled band, excluding DC. :meth:`plot_output_fft` must
        run first.

        Returns
        -------
        float
            SQNR in dB, or infinity when the noise power is zero.

        Raises
        ------
        ValueError
            If the FFT has not been calculated.
        """
        if self._fft_data is None:
            raise ValueError(
                "plot_output_fft must be run first to populate FFT data."
            )
        fft_data = self._fft_data
        count = len(fft_data)
        positive = fft_data[3:count // 2]
        peak_index = np.argmax(np.abs(positive)) + 1
        power = np.abs(fft_data) ** 2
        signal_bins = np.arange(peak_index - 2, peak_index + 3)
        signal_power = np.sum(power[signal_bins])
        noise_bins = np.arange(4, count // (2 * self._reg["osr"]))
        noise_power = np.sum(power[noise_bins]) - signal_power
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
    """Tests the phase step and the amplitude-to-magnitude mapping."""

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

    def test_tuning_word_is_one_shifted_by_frequency(self) -> None:
        """Tests ``step = 1 << frequency``, including the half-turn end."""
        dac = self._converter()
        for code in range(16):
            dac.set_frequency(code)
            self.assertEqual(dac._phase_step(), 1 << code)
        dac.set_frequency(0)
        slow = dac.convert(4)
        np.testing.assert_array_equal(
            slow["phase"], np.array([0, 1, 2, 3], dtype=np.uint16)
        )
        dac.set_frequency(15)
        fast = dac.convert(4)
        half_turn = 1 << (PHASE_BITS - 1)
        np.testing.assert_array_equal(
            fast["phase"],
            np.array([0, half_turn, 0, half_turn], dtype=np.uint16),
        )
        with self.assertRaises(ValueError):
            dac.set_frequency(16)

    def test_amplitude_is_the_cordic_initial_magnitude(self) -> None:
        """Tests that code 14 rotates a half-scale vector, not a product."""
        dac = self._converter()
        dac.set_amplitude(14)
        dac.set_frequency(0)
        frame = dac.convert(32)
        cosine, sine = dac._cordic.rotate(
            0.5, 0, frame["phase"].to_numpy()
        )
        np.testing.assert_array_equal(frame["cordic_cos"], cosine.values)
        np.testing.assert_array_equal(frame["cordic_sin"], sine.values)
        self.assertEqual(dac._vector_magnitude(), 0.5)

    def test_full_scale_keeps_gain_compensation_and_saturation(self) -> None:
        """Tests ``1/K`` and signed saturation at amplitude code 15."""
        dac = self._converter()
        dac.set_amplitude(FULL_SCALE_AMPLITUDE)
        dac.set_frequency(0)
        # Phase equals the sample index, so index 8192 is pi/4.
        frame = dac.convert(8193)
        quarter = frame.iloc[8192]
        scale = float(1 << (dac._n_cordic_bits - 1))
        cosine = float(quarter["cordic_cos"]) / scale
        sine = float(quarter["cordic_sin"]) / scale
        expected = math.sqrt(2.0) / 2.0
        self.assertAlmostEqual(cosine, expected, delta=0.01)
        self.assertAlmostEqual(sine, expected, delta=0.01)
        # K * cos(pi/4) is about 1.16 and would saturate near 1.
        self.assertLess(abs(cosine), 0.9)
        self.assertLess(abs(sine), 0.9)
        limit = (1 << (dac._n_cordic_bits - 1)) - 1
        self.assertLessEqual(int(frame["cordic_cos"].max()), limit)
        self.assertGreaterEqual(int(frame["cordic_cos"].min()), -limit - 1)
        unit_cos, unit_sin = dac._cordic.rotate(1, 0, np.array([8192]))
        self.assertEqual(int(quarter["cordic_cos"]), int(unit_cos.values[0]))
        self.assertEqual(int(quarter["cordic_sin"]), int(unit_sin.values[0]))


def main() -> None:
    """Plot one DAC waveform with and without the delta-sigma modulator."""
    print("Running SineGenDAC test without DSM...")
    dac = SineGenDAC()
    dac.set_frequency(0x1)
    dac.set_amplitude(0xE)
    dac.set_osr(64)
    dac.set_dac_mode(dac_number=0, mode="AC")
    dac.set_dac_mode(dac_number=1, mode="AC")

    n_cycles = 2**16
    n_plot_cycles = 750
    dac.convert(n_cycles)

    figure, (time_axis, spectrum_axis) = plt.subplots(1, 2, figsize=(15, 6))
    dac.plot_output(n_plot_cycles, ax=time_axis)
    dac.plot_output_fft(ax=spectrum_axis)
    sqnr_no_dsm = dac.get_sqnr_db()
    time_axis.lines[-2].set_label("DACP Output (No DSM)")
    time_axis.lines[-1].set_label("DACN Output (No DSM)")

    print("Running SineGenDAC test with DSM...")
    dac.set_dsm_enable(enable=True)
    dac.convert(n_cycles)

    dac.plot_output(n_plot_cycles, ax=time_axis)
    dac.plot_output_fft(ax=spectrum_axis, add_osrline=True)
    sqnr_dsm = dac.get_sqnr_db()
    time_axis.lines[-2].set_label("DACP Output (With DSM)")
    time_axis.lines[-1].set_label("DACN Output (With DSM)")

    spectrum_axis.lines[-3].set_label(
        f"SQNR={np.round(sqnr_no_dsm, 3)}, NO DSM"
    )
    spectrum_axis.lines[-2].set_label(
        f"SQNR={np.round(sqnr_dsm, 3)}, WITH DSM"
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

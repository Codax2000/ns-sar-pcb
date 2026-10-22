"""Differential DAC values and voltages from a scaled cosine.
"""

from __future__ import annotations

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


def _check_registers(
    n_samples: int,
    frequency: int,
    amplitude_scale: int,
    amplitude: int,
    dacp_mode: str,
    dacn_mode: str,
    dacp_dc_value: int,
    dacn_dc_value: int,
) -> None:
    """Raise unless the sample count and DAC settings are valid."""
    _check_n_samples(n_samples)
    _check_frequency(frequency)
    _check_amplitude_scale(amplitude_scale)
    _check_amplitude(amplitude)
    _check_dac_mode(dacp_mode, "dacp")
    _check_dac_mode(dacn_mode, "dacn")
    _check_dc_value(dacp_dc_value, "dacp")
    _check_dc_value(dacn_dc_value, "dacn")


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
    _check_registers(
        n_samples,
        frequency,
        amplitude_scale,
        amplitude,
        dacp_mode,
        dacn_mode,
        dacp_dc_value,
        dacn_dc_value,
    )
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
    ).reshape(-1)
    cosine = cosine >> (15 - amplitude)
    if dsm_enable:
        dac_signed, error = _modulate_dsm(np.ascontiguousarray(cosine))
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


def _windowed_dacp_spectrum(
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
    spectrum = _windowed_dacp_spectrum(results, warmup_samples)
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
    spectrum = _windowed_dacp_spectrum(results, warmup_samples)
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

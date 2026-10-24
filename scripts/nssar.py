"""Noise-shaping SAR conversion of a differential input.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fp_array import FixedPointArray


DEFAULT_OSR = 32
BLACKMAN_HALF_WIDTH = 3
_COUNTER_FRACTIONAL_BITS = 0

_RESULT_COLUMNS = (
    "input",
    "sample_input",
    "integrator_input",
    "vin_p",
    "vin_n",
    "vint_p",
    "vint_n",
    "quantizer_decision",
    "dac_feedback",
    "error",
    "integrator_1",
    "integrator_2",
    "incremental_1",
    "incremental_2",
    "reset",
    "sample_output",
    "dwa_pointer",
)


def _check_voltage_array(values: np.ndarray, name: str) -> None:
    """Raise unless values is a non-empty 1-D real array."""
    if not isinstance(values, np.ndarray):
        received = type(values).__name__
        raise TypeError(f"{name} must be a numpy array, got {received}")
    if values.ndim != 1:
        raise ValueError(f"{name} must be 1-D, got shape {values.shape}")
    is_real = np.issubdtype(values.dtype, np.floating) or np.issubdtype(
        values.dtype, np.integer
    )
    if not is_real:
        raise TypeError(
            f"{name} must have a real numeric dtype, got {values.dtype}"
        )
    if values.size < 1:
        raise ValueError(
            f"{name} must contain at least 1 sample, got {values.size}"
        )
    n_bad = int(np.size(values) - np.isfinite(values).sum())
    if n_bad:
        raise ValueError(
            f"{name} must contain only finite values, got {n_bad} "
            "non-finite"
        )


def _check_same_length(vin_p: np.ndarray, vin_n: np.ndarray) -> None:
    """Raise unless vin_p and vin_n have the same length."""
    if vin_p.shape[0] != vin_n.shape[0]:
        raise ValueError(
            "vin_p and vin_n must have the same length, "
            f"got {vin_p.shape[0]} and {vin_n.shape[0]}"
        )


def _check_flag(flag: bool, name: str) -> None:
    """Raise unless flag is a bool."""
    if not isinstance(flag, bool):
        received = type(flag).__name__
        raise TypeError(f"{name} must be a bool, got {received}")


def _check_quantizer_bits(n_quantizer_bits: int) -> None:
    """Raise unless n_quantizer_bits is an int from 1 to 16."""
    if isinstance(n_quantizer_bits, bool) or not isinstance(
        n_quantizer_bits, int
    ):
        received = type(n_quantizer_bits).__name__
        raise TypeError(
            f"n_quantizer_bits must be an int, got {received}"
        )
    if n_quantizer_bits < 1 or n_quantizer_bits > 16:
        raise ValueError(
            "n_quantizer_bits must be from 1 to 16, "
            f"got {n_quantizer_bits}"
        )


def _check_mismatch_sigma(cap_mismatch_sigma: float) -> None:
    """Raise unless cap_mismatch_sigma is a non-negative finite real."""
    if isinstance(cap_mismatch_sigma, bool) or not isinstance(
        cap_mismatch_sigma, (int, float)
    ):
        received = type(cap_mismatch_sigma).__name__
        raise TypeError(
            "cap_mismatch_sigma must be a real number, "
            f"got {received}"
        )
    if not np.isfinite(cap_mismatch_sigma):
        raise ValueError(
            "cap_mismatch_sigma must be finite, "
            f"got {cap_mismatch_sigma}"
        )
    if cap_mismatch_sigma < 0:
        raise ValueError(
            "cap_mismatch_sigma must be non-negative, "
            f"got {cap_mismatch_sigma}"
        )


def _check_reference(voltage: float, name: str) -> None:
    """Raise unless voltage is a finite real number."""
    if isinstance(voltage, bool) or not isinstance(voltage, (int, float)):
        received = type(voltage).__name__
        raise TypeError(f"{name} must be a real number, got {received}")
    if not np.isfinite(voltage):
        raise ValueError(f"{name} must be finite, got {voltage}")


def _check_distinct_references(vrefp: float, vrefn: float) -> None:
    """Raise unless the two references are different."""
    if vrefp == vrefn:
        raise ValueError(
            f"vrefp and vrefn must differ, got {vrefp} and {vrefn}"
        )


def _check_osr(osr: int) -> None:
    """Raise unless osr is a positive int."""
    if isinstance(osr, bool) or not isinstance(osr, int):
        received = type(osr).__name__
        raise TypeError(f"osr must be an int, got {received}")
    if osr < 1:
        raise ValueError(f"osr must be a positive int, got {osr}")


def _make_capacitors(
    n_quantizer_bits: int, cap_mismatch_sigma: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return the positive and negative capacitor arrays."""
    count = 2 ** n_quantizer_bits
    if cap_mismatch_sigma == 0:
        ones = np.ones(count)
        return ones, ones.copy()
    positive = np.random.normal(1.0, cap_mismatch_sigma, count)
    negative = np.random.normal(1.0, cap_mismatch_sigma, count)
    return positive, negative


def _make_control_signals(
    n_samples: int, osr: int, incremental_mode: bool
) -> tuple[np.ndarray, np.ndarray]:
    """Return reset and sample_output for each sample clock."""
    clocks = np.arange(n_samples)
    reset = np.zeros(n_samples, dtype=bool)
    reset[0] = True
    if incremental_mode:
        reset[clocks % osr == 0] = True
    sample_output = (clocks % osr) == (osr - 1)
    return reset, sample_output


def _update_capacitor_voltages(
    cap_voltages: np.ndarray,
    bit_index: int,
    bit: bool,
    vrefp: float,
    vrefn: float,
    vcm: float,
) -> np.ndarray:
    """Connect the next group of capacitors to a reference."""
    n_bits = int(np.log2(cap_voltages.shape[0]))
    n_update = 2 ** (n_bits - (bit_index + 1))
    unset = np.flatnonzero(cap_voltages == vcm)
    if bit:
        cap_voltages[unset[:n_update]] = vrefp
    else:
        cap_voltages[unset[-(n_update + 1):-1]] = vrefn
    return cap_voltages


def _decision_from_bits(bits: np.ndarray) -> int:
    """Return the integer weight of the quantizer comparisons."""
    weight = bits.shape[0] - 1
    decision = 0
    for index in range(bits.shape[0]):
        if bits[index]:
            decision += 1 << (weight - index)
    return decision


def _run_sar(
    vin_p: float,
    vin_n: float,
    vint_p: float,
    vint_n: float,
    cap_p: np.ndarray,
    cap_n: np.ndarray,
    pointer: int,
    vrefp: float,
    vrefn: float,
) -> tuple[int, float]:
    """Return one quantizer decision and the capacitor-array feedback."""
    n_bits = int(np.log2(len(cap_p)))
    rolled_p = np.roll(cap_p, -pointer)
    rolled_n = np.roll(cap_n, -pointer)
    vcm = (vrefp + vrefn) / 2.0
    positive_voltage = np.zeros(n_bits + 1)
    negative_voltage = np.zeros(n_bits + 1)
    bits = np.zeros(n_bits, dtype=int)
    cap_voltages = np.full(2 ** n_bits, vcm)
    positive_voltage[0] = vrefp - vin_p
    negative_voltage[0] = vrefp - vin_n
    for index in range(n_bits):
        bit = bool(
            vint_p + negative_voltage[index]
            >= vint_n + positive_voltage[index]
        )
        bits[index] = int(bit)
        cap_voltages = _update_capacitor_voltages(
            cap_voltages, index, bit, vrefp, vrefn, vcm
        )
        inverted = (vrefp + vrefn) - cap_voltages
        charge_p = np.sum(rolled_p * cap_voltages) + np.sum(rolled_p) * (
            positive_voltage[0] - vcm
        )
        charge_n = np.sum(rolled_n * inverted) + np.sum(rolled_n) * (
            negative_voltage[0] - vcm
        )
        positive_voltage[index + 1] = charge_p / np.sum(rolled_p)
        negative_voltage[index + 1] = charge_n / np.sum(rolled_n)
    decision = _decision_from_bits(bits)
    feedback = float(negative_voltage[n_bits] - positive_voltage[n_bits])
    return decision, feedback


def _integrate_decisions(
    decisions: np.ndarray, reset: np.ndarray, n_quantizer_bits: int
) -> tuple[np.ndarray, np.ndarray]:
    """Return the two incremental counts in signed integer format (n, 0)."""
    decision_width = n_quantizer_bits + 1
    count = decisions.shape[0]
    first: list[int] = []
    second: list[int] = []
    previous_1: FixedPointArray | None = None
    previous_2: FixedPointArray | None = None
    for index in range(count):
        decision = int(decisions[index])
        if reset[index]:
            current_1 = FixedPointArray.from_mantissas(
                decision, decision_width, _COUNTER_FRACTIONAL_BITS
            )
            current_2 = FixedPointArray.from_mantissas(
                decision, decision_width, _COUNTER_FRACTIONAL_BITS
            )
        else:
            current_1 = previous_1 + decision
            current_2 = current_1 + previous_2
        first.append(int(current_1.get_mantissas()[0]))
        second.append(int(current_2.get_mantissas()[0]))
        previous_1 = current_1
        previous_2 = current_2
    return _integers_to_array(first), _integers_to_array(second)


def _integers_to_array(values: list[int]) -> np.ndarray:
    """Return values as int64, or as Python integers if they do not fit."""
    low = -(1 << 63)
    high = (1 << 63) - 1
    if min(values) < low or max(values) > high:
        return np.array(values, dtype=object)
    return np.array(values, dtype=np.int64)


def _run_conversion(
    vin_p: np.ndarray,
    vin_n: np.ndarray,
    do_dwa: bool,
    incremental_mode: bool,
    reset_dwa: bool,
    n_quantizer_bits: int,
    cap_mismatch_sigma: float,
    vrefp: float,
    vrefn: float,
    osr: int,
) -> pd.DataFrame:
    """Convert checked inputs and return one row per sample clock."""
    n_samples = vin_p.shape[0]
    differential = vin_p - vin_n
    reset, sample_output = _make_control_signals(
        n_samples, osr, incremental_mode
    )
    cap_p, cap_n = _make_capacitors(n_quantizer_bits, cap_mismatch_sigma)
    vcm = (vrefp + vrefn) / 2.0
    sample_input = differential.copy()
    integrator_input = np.zeros(n_samples)
    quantizer_vin_p = np.zeros(n_samples)
    quantizer_vin_n = np.zeros(n_samples)
    quantizer_vint_p = np.zeros(n_samples)
    quantizer_vint_n = np.zeros(n_samples)
    decision = np.zeros(n_samples, dtype=np.int64)
    dac_feedback = np.zeros(n_samples)
    integrator_1 = np.zeros(n_samples)
    integrator_2 = np.zeros(n_samples)
    dwa_pointer = np.zeros(n_samples, dtype=np.int64)
    n_capacitors = cap_p.shape[0]
    pointer = 0
    for index in range(n_samples):
        if reset[index]:
            integrator_input[index] = 0.0
        else:
            integrator_input[index] = (
                2.0 * integrator_1[index - 1] + integrator_2[index - 1]
            )
        quantizer_vint_p[index] = vcm + integrator_input[index] / 2.0
        quantizer_vint_n[index] = vcm - integrator_input[index] / 2.0
        quantizer_vin_p[index] = vcm + sample_input[index] / 2.0
        quantizer_vin_n[index] = vcm - sample_input[index] / 2.0
        if (
            index == 0
            or not do_dwa
            or (reset[index] and do_dwa and reset_dwa)
        ):
            used_pointer = 0
        else:
            used_pointer = pointer
        decision[index], dac_feedback[index] = _run_sar(
            float(quantizer_vin_p[index]),
            float(quantizer_vin_n[index]),
            float(quantizer_vint_p[index]),
            float(quantizer_vint_n[index]),
            cap_p,
            cap_n,
            used_pointer,
            vrefp,
            vrefn,
        )
        pointer = (used_pointer + int(decision[index])) % n_capacitors
        dwa_pointer[index] = pointer
        if reset[index]:
            integrator_1[index] = dac_feedback[index]
            integrator_2[index] = 0.0
        else:
            integrator_1[index] = (
                dac_feedback[index] + integrator_1[index - 1]
            )
            integrator_2[index] = (
                integrator_1[index - 1] + integrator_2[index - 1]
            )
    incremental_1, incremental_2 = _integrate_decisions(
        decision, reset, n_quantizer_bits
    )
    frame = pd.DataFrame(
        {
            "input": differential,
            "sample_input": sample_input,
            "integrator_input": integrator_input,
            "vin_p": quantizer_vin_p,
            "vin_n": quantizer_vin_n,
            "vint_p": quantizer_vint_p,
            "vint_n": quantizer_vint_n,
            "quantizer_decision": decision,
            "dac_feedback": dac_feedback,
            "error": dac_feedback.copy(),
            "integrator_1": integrator_1,
            "integrator_2": integrator_2,
            "incremental_1": incremental_1,
            "incremental_2": incremental_2,
            "reset": reset,
            "sample_output": sample_output,
            "dwa_pointer": dwa_pointer,
        }
    )
    return frame.loc[:, list(_RESULT_COLUMNS)]


def convert_nssar(
    vin_p: np.ndarray,
    vin_n: np.ndarray,
    do_dwa: bool = True,
    incremental_mode: bool = True,
    reset_dwa: bool = False,
    n_quantizer_bits: int = 3,
    cap_mismatch_sigma: float = 0.0,
    vrefp: float = 1.0,
    vrefn: float = 0.0,
    osr: int = DEFAULT_OSR,
) -> pd.DataFrame:
    """Return one row per sample clock for the noise-shaping SAR.

    Call it with a register dictionary, for example
    ``convert_nssar(vin_p, vin_n, **registers)``.

    Parameters
    ----------
    vin_p : numpy.ndarray
        Positive input voltage, one value per sample clock.
    vin_n : numpy.ndarray
        Negative input voltage, one value per sample clock.
        Same length as ``vin_p``.
    do_dwa : bool, optional
        True rotates the capacitors from the data-weighted averaging
        pointer. Default is True.
    incremental_mode : bool, optional
        True resets the integrators and counters every ``osr``
        clocks. Default is True.
    reset_dwa : bool, optional
        True clears the averaging pointer when the integrators reset.
        Default is False.
    n_quantizer_bits : int, optional
        Number of SAR decisions, from 1 to 16. Default is 3.
    cap_mismatch_sigma : float, optional
        Standard deviation of each capacitor value about 1.
        Default is 0.
    vrefp : float, optional
        Positive reference voltage. Default is 1.
    vrefn : float, optional
        Negative reference voltage. Default is 0.
    osr : int, optional
        Clocks per output sample. Default is 32.

    Returns
    -------
    pandas.DataFrame
        One row per sample clock. Columns are ``input``,
        ``sample_input``, ``integrator_input``, ``vin_p``, ``vin_n``,
        ``vint_p``, ``vint_n``, ``quantizer_decision``,
        ``dac_feedback``, ``error``, ``integrator_1``,
        ``integrator_2``, ``incremental_1``, ``incremental_2``,
        ``reset``, ``sample_output``, and ``dwa_pointer``.
        ``incremental_1`` and ``incremental_2`` are signed integer
        counts, format ``(n, 0)``, with ``n`` wide enough to hold
        the count.

    Raises
    ------
    TypeError
        If an argument has the wrong type.
    ValueError
        If a length, count, reference, or deviation is out of range.
    """
    _check_voltage_array(vin_p, "vin_p")
    _check_voltage_array(vin_n, "vin_n")
    _check_same_length(vin_p, vin_n)
    _check_flag(do_dwa, "do_dwa")
    _check_flag(incremental_mode, "incremental_mode")
    _check_flag(reset_dwa, "reset_dwa")
    _check_quantizer_bits(n_quantizer_bits)
    _check_mismatch_sigma(cap_mismatch_sigma)
    _check_reference(vrefp, "vrefp")
    _check_reference(vrefn, "vrefn")
    _check_distinct_references(vrefp, vrefn)
    _check_osr(osr)
    return _run_conversion(
        np.asarray(vin_p, dtype=np.float64),
        np.asarray(vin_n, dtype=np.float64),
        do_dwa,
        incremental_mode,
        reset_dwa,
        n_quantizer_bits,
        float(cap_mismatch_sigma),
        float(vrefp),
        float(vrefn),
        osr,
    )


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
        raise ValueError(
            f"results must contain at least 1 row, got {n_rows}"
        )
    if warmup_samples < 0 or warmup_samples >= n_rows:
        raise ValueError(
            "warmup_samples must be between 0 and "
            f"{n_rows - 1}, got {warmup_samples}"
        )


def _check_sample_rate(fs: float) -> None:
    """Raise unless fs is a positive real sample rate."""
    if isinstance(fs, bool) or not isinstance(fs, (int, float)):
        received = type(fs).__name__
        raise TypeError(f"fs must be a real number, got {received}")
    if not np.isfinite(fs):
        raise ValueError(f"fs must be finite, got {fs}")
    if fs <= 0:
        raise ValueError(f"fs must be positive, got {fs}")


def _check_n_samples(n_samples: int) -> None:
    """Raise unless n_samples is a positive int."""
    if isinstance(n_samples, bool) or not isinstance(n_samples, int):
        received = type(n_samples).__name__
        raise TypeError(f"n_samples must be an int, got {received}")
    if n_samples < 1:
        raise ValueError(f"n_samples must be positive, got {n_samples}")


def _decimated_output(
    results: pd.DataFrame, warmup_samples: int
) -> np.ndarray:
    """Return incremental_2 at each sample_output after warmup."""
    _check_column(results, "incremental_2")
    _check_column(results, "sample_output")
    _check_warmup_samples(warmup_samples, len(results))
    kept = results.iloc[warmup_samples:]
    flags = np.asarray(kept["sample_output"], dtype=bool)
    if not flags.any():
        raise ValueError(
            "results must include a sample_output after warmup, got none"
        )
    values = kept["incremental_2"].to_numpy()[flags]
    return np.asarray(values, dtype=np.float64)


def _quantizer_samples(
    results: pd.DataFrame, warmup_samples: int
) -> np.ndarray:
    """Return quantizer decisions after warmup."""
    _check_column(results, "quantizer_decision")
    _check_warmup_samples(warmup_samples, len(results))
    return np.asarray(
        results["quantizer_decision"].iloc[warmup_samples:],
        dtype=np.float64,
    )


def _windowed_spectrum(samples: np.ndarray) -> np.ndarray:
    """Return the Blackman FFT of samples."""
    window = np.blackman(samples.shape[0])
    return np.fft.fft(samples * window)


def _band_powers(
    spectrum: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Return power, signal bins, noise bins, and the peak bin."""
    count = spectrum.shape[0]
    nyquist = count // 2
    guard = BLACKMAN_HALF_WIDTH
    if nyquist <= guard:
        raise ValueError(
            "spectrum does not clear the DC leakage bins, "
            f"got {count} samples"
        )
    power = np.abs(spectrum) ** 2
    search = np.arange(guard + 1, nyquist + 1)
    peak = int(search[np.argmax(power[search])])
    signal_bins = np.arange(peak - guard, peak + guard + 1)
    signal_bins = signal_bins[
        (signal_bins >= 0) & (signal_bins <= nyquist)
    ]
    noise_bins = search[~np.isin(search, signal_bins)]
    return power, signal_bins, noise_bins, peak


def _plot_normalized_spectrum(
    axis: plt.Axes,
    frequencies: np.ndarray,
    spectrum: np.ndarray,
    label: str,
) -> None:
    """Plot one-sided power in dB, normalized to the peak past DC."""
    power = np.abs(spectrum) ** 2
    nyquist = spectrum.shape[0] // 2
    search = np.arange(BLACKMAN_HALF_WIDTH + 1, nyquist + 1)
    if search.size:
        peak = float(np.max(power[search]))
    else:
        peak = float(np.max(power))
    if peak == 0.0:
        power_db = np.zeros(power.shape)
    else:
        with np.errstate(divide="ignore"):
            power_db = 10.0 * np.log10(power / peak)
    positive = frequencies >= 0
    axis.plot(frequencies[positive], power_db[positive], label=label)


def calculate_sndr_db(
    results: pd.DataFrame, warmup_samples: int = 0
) -> float:
    """Return the signal-to-noise-and-distortion ratio in dB.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`convert_nssar`.
    warmup_samples : int, optional
        Leading sample clocks left out of the measurement.
        Default is 0.

    Returns
    -------
    float
        Ratio in dB of the output tone to the rest of the
        decimated band. Infinity when the noise power is zero.
        The output samples are ``incremental_2`` where
        ``sample_output`` is true.

    Raises
    ------
    TypeError
        If ``warmup_samples`` has the wrong type.
    ValueError
        If the warmup or the table is unusable.
    """
    samples = _decimated_output(results, warmup_samples)
    spectrum = _windowed_spectrum(samples)
    power, signal_bins, noise_bins, _peak = _band_powers(spectrum)
    signal_power = float(np.sum(power[signal_bins]))
    if noise_bins.size == 0:
        return float("inf")
    noise_power = float(np.sum(power[noise_bins]))
    if noise_power == 0.0:
        return float("inf")
    return float(10.0 * np.log10(signal_power / noise_power))


def calculate_sfdr_db(
    results: pd.DataFrame, warmup_samples: int = 0
) -> float:
    """Return the spurious-free dynamic range in dB.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`convert_nssar`.
    warmup_samples : int, optional
        Leading sample clocks left out of the measurement.
        Default is 0.

    Returns
    -------
    float
        Ratio in dB of the output tone to the largest other bin
        in the decimated band. Infinity when that bin is zero.
        The output samples are ``incremental_2`` where
        ``sample_output`` is true.

    Raises
    ------
    TypeError
        If ``warmup_samples`` has the wrong type.
    ValueError
        If the warmup or the table is unusable.
    """
    samples = _decimated_output(results, warmup_samples)
    spectrum = _windowed_spectrum(samples)
    power, _signal_bins, noise_bins, peak = _band_powers(spectrum)
    if noise_bins.size == 0:
        return float("inf")
    noise_power = float(np.max(power[noise_bins]))
    if noise_power == 0.0:
        return float("inf")
    signal_power = float(power[peak])
    return float(10.0 * np.log10(signal_power / noise_power))


def plot_output(
    results: pd.DataFrame,
    fs: float,
    n_samples: int,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot the decimated incremental output against time.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`convert_nssar`.
    fs : float
        Sample rate of the input clocks, in hertz.
    n_samples : int
        Number of output samples to plot, taken where
        ``sample_output`` is true.
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
    _check_column(results, "sample_output")
    _check_column(results, "incremental_2")
    clocks = np.flatnonzero(
        np.asarray(results["sample_output"], dtype=bool)
    )
    if n_samples > clocks.size:
        raise ValueError(
            f"n_samples must be at most {int(clocks.size)}, "
            f"got {n_samples}"
        )
    if ax is None:
        figure, axis = plt.subplots(figsize=(10, 6))
    else:
        figure = ax.figure
        axis = ax
    chosen = clocks[:n_samples]
    axis.plot(
        chosen / fs,
        results["incremental_2"].iloc[list(chosen)],
        label="Output",
    )
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Incremental output")
    axis.set_title("ADC output")
    axis.legend()
    axis.grid()
    return figure


def plot_spectrum(
    results: pd.DataFrame,
    fs: float,
    osr: int = DEFAULT_OSR,
    warmup_samples: int = 0,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot the decimated output spectrum after skipping warmup.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`convert_nssar`.
    fs : float
        Sample rate of the input clocks, in hertz.
    osr : int, optional
        Clocks per output sample. The frequency axis uses
        ``fs / osr``. Default is 32.
    warmup_samples : int, optional
        Leading sample clocks left out of the spectrum. Default is 0.
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
    _check_osr(osr)
    samples = _decimated_output(results, warmup_samples)
    spectrum = _windowed_spectrum(samples)
    frequencies = np.fft.fftfreq(samples.shape[0], d=osr / fs)
    if ax is None:
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.set_xscale("log")
    else:
        figure = ax.figure
        axis = ax
    _plot_normalized_spectrum(axis, frequencies, spectrum, "Output")
    axis.set_xlabel("Frequency [Hz]")
    axis.set_ylabel("Magnitude [dB]")
    axis.set_title("ADC output spectrum")
    axis.legend()
    axis.grid(True, which="both", ls="-")
    return figure


def plot_quantizer_spectrum(
    results: pd.DataFrame,
    fs: float,
    osr: int | None = None,
    warmup_samples: int = 0,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot the quantizer spectrum after skipping warmup clocks.

    Parameters
    ----------
    results : pandas.DataFrame
        Table from :func:`convert_nssar`.
    fs : float
        Sample rate of the input clocks, in hertz.
    osr : int or None, optional
        Draw the band edge at half the sample rate divided by this
        value. ``None`` draws no edge. Default is ``None``.
    warmup_samples : int, optional
        Leading sample clocks left out of the spectrum. Default is 0.
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
    samples = _quantizer_samples(results, warmup_samples)
    spectrum = _windowed_spectrum(samples)
    frequencies = np.fft.fftfreq(samples.shape[0], d=1.0 / fs)
    if ax is None:
        figure, axis = plt.subplots(figsize=(10, 6))
        axis.set_xscale("log")
    else:
        figure = ax.figure
        axis = ax
    _plot_normalized_spectrum(axis, frequencies, spectrum, "Quantizer")
    if osr is not None:
        cutoff_hz = (fs / 2.0) / osr
        cutoff_mhz = np.round(cutoff_hz / 1e6, 3)
        axis.axvline(
            x=cutoff_hz,
            color="r",
            linestyle="--",
            linewidth=1.5,
            label=f"$OSR={osr}$, $f_{{max}}={cutoff_mhz}$ MHz",
        )
    axis.set_xlabel("Frequency [Hz]")
    axis.set_ylabel("Magnitude [dB]")
    axis.set_title("Quantizer spectrum")
    axis.legend()
    axis.grid(True, which="both", ls="-")
    return figure


def main() -> None:
    """Plot one conversion and compare data-weighted averaging.

    The tone sits on a bin of the decimated output. The sample rate
    is 100 MHz and the oversampling ratio is 32. Mismatched
    capacitors are redrawn from the same seed for each averaging mode.
    """
    fs = 100e6
    osr = DEFAULT_OSR
    n_output = 1024
    n_samples = n_output * osr
    prime = 97
    frequency = fs * prime / (16 * n_output)
    amplitude = 0.4
    clocks = np.arange(n_samples)
    differential = amplitude * np.cos(2.0 * np.pi * frequency * clocks / fs)
    vin_p = 0.5 + differential / 2.0
    vin_n = 0.5 - differential / 2.0
    print("Running conversion...")
    results = convert_nssar(
        vin_p,
        vin_n,
        do_dwa=True,
        incremental_mode=True,
        reset_dwa=True,
        osr=osr,
    )
    figure, (time_axis, spectrum_axis) = plt.subplots(1, 2, figsize=(15, 6))
    plot_output(results, fs, 64, ax=time_axis)
    plot_spectrum(results, fs, osr=osr, ax=spectrum_axis)
    sndr = calculate_sndr_db(results)
    sfdr = calculate_sfdr_db(results)
    print(f"SNDR {sndr:.2f} dB")
    print(f"SFDR {sfdr:.2f} dB")
    quantizer = plot_quantizer_spectrum(results, fs, osr=osr)
    figure.tight_layout()
    figure.savefig("./adc_output.png")
    quantizer.savefig("./adc_quantizer_spectrum.png")

    print("Comparing data-weighted averaging...")
    figure, axis = plt.subplots(figsize=(10, 6))
    cases = (
        ("DWA with reset", True, True, "k"),
        ("DWA without reset", True, False, "b"),
        ("No DWA", False, False, "r"),
    )
    for label, do_dwa, reset_dwa, color in cases:
        np.random.seed(1)
        frame = convert_nssar(
            vin_p,
            vin_n,
            osr=osr,
            do_dwa=do_dwa,
            incremental_mode=True,
            reset_dwa=reset_dwa,
            cap_mismatch_sigma=0.02,
        )
        plot_spectrum(frame, fs, osr=osr, ax=axis)
        reading = calculate_sndr_db(frame)
        print(f"{label} SNDR {reading:.2f} dB")
        axis.lines[-1].set_label(f"{label}, SNDR={np.round(reading, 1)} dB")
        axis.lines[-1].set_color(color)
    axis.legend()
    axis.set_xscale("log")
    figure.tight_layout()
    figure.savefig("./adc_dwa_compare.png")
    print("Done.")


if __name__ == "__main__":
    main()

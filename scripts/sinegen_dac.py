"""Differential DAC values and voltages from a scaled cosine.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

from cordic import cordic_rotate
from fp_array import FixedPointArray


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

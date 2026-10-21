"""Rotation-mode CORDIC sine and cosine.

Phase is an unsigned 16-bit fraction of one turn (U0.16). ``x`` and
``y`` are signed fixed-point values. The vector format is ``(n, r)``:
16 bits with 13 fractional bits by default, or 15 fractional bits for
the sine generator.
"""

from __future__ import annotations

import argparse
import math
import numbers
import unittest
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from fp_array import FixedPointArray


PHASE_BITS = 16
OFFSET_BITS = 14
# Wide enough for the remaining angle and one arctangent step past zero.
ANGLE_WIDTH = 16
SCALE_BITS = 4
# Largest constant that keeps x and y in signed 16 bits for every
# amplitude scale and every phase. 21224 does not.
PRELOAD_C = 21223


def cordic_gain(n_rotations: int) -> float:
    """Return the CORDIC gain for ``n_rotations`` iterations.

    Parameters
    ----------
    n_rotations : int
        Number of iterations. Zero returns 1.

    Returns
    -------
    float
        Gain ``K``.

    Raises
    ------
    ValueError
        If ``n_rotations`` is negative or not an integer.
    """
    if isinstance(n_rotations, bool) or not isinstance(
        n_rotations, numbers.Integral
    ):
        raise ValueError("n_rotations must be a non-negative integer")
    if n_rotations < 0:
        raise ValueError("n_rotations must be a non-negative integer")
    gain = 1.0
    for index in range(int(n_rotations)):
        # Iteration i multiplies the length by sqrt(1 + 2**(-2*i)).
        gain *= math.sqrt(1.0 + 2.0 ** (-2 * index))
    return gain


def scale_preload(constant: int, scale: int) -> int:
    """Return the initial x code for a 4-bit amplitude scale.

    Parameters
    ----------
    constant : int
        Magnitude constant, in the same integer units as ``x``.
    scale : int
        Amplitude scale from 0 to 15. Weight is ``scale / 16``.

    Returns
    -------
    int
        Initial x code.

    Raises
    ------
    ValueError
        If ``scale`` is outside 0 to 15.
    """
    if isinstance(scale, bool) or not isinstance(scale, numbers.Integral):
        raise ValueError("scale must be an integer from 0 to 15")
    if scale < 0 or scale > (1 << SCALE_BITS) - 1:
        raise ValueError("scale must be an integer from 0 to 15")
    total = 0
    for bit in range(SCALE_BITS):
        if (int(scale) >> bit) & 1:
            # Bit 0 is the LSB. The shift truncates toward -infinity.
            total += int(constant) >> (SCALE_BITS - bit)
    return total


def _rounded_angle_codes(n_rotations: int) -> list[int]:
    """Return arctangent table codes as fractions of a turn.

    Parameters
    ----------
    n_rotations : int
        Number of entries, one per iteration.

    Returns
    -------
    list of int
        Entry ``i`` is ``atan(2**(-i)) / (2*pi)`` rounded to the
        nearest U0.16 code.
    """
    scale = 1 << PHASE_BITS
    codes = []
    for index in range(n_rotations):
        turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
        # Round half up. These values are positive.
        codes.append(int(math.floor(turns * scale + 0.5)))
    return codes


def _quadrant_mux(
    quadrant: np.ndarray,
    choices: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    """Select one integer array for each quadrant code.

    Parameters
    ----------
    quadrant : numpy.ndarray
        Quadrant codes 0, 1, 2, and 3.
    choices : tuple of numpy.ndarray
        One array per quadrant, broadcastable with ``quadrant``.

    Returns
    -------
    numpy.ndarray
        ``choices[quadrant]`` at each element.
    """
    selected = choices[0]
    for code in range(1, 4):
        selected = np.where(quadrant == code, choices[code], selected)
    return selected


class CORDIC:
    """Rotation-mode CORDIC.

    ``x`` and ``y`` are signed ``(n_x, r_x)``. Phase is an unsigned
    16-bit fraction of a turn. :meth:`rotate_preload` takes the 4-bit
    amplitude scale and sets the initial magnitude from it.
    """

    def __init__(
        self,
        n_rotations: int = 16,
        n_x: int = 16,
        r_x: int = 13,
    ) -> None:
        """Build the arctangent table.

        Parameters
        ----------
        n_rotations : int, optional
            Number of iterations. Default is 16.
        n_x : int, optional
            Signed width of ``x`` and ``y``. Default is 16.
        r_x : int, optional
            Fractional bits of ``x`` and ``y``. Default is 13.

        Raises
        ------
        ValueError
            If an iteration count or format is not valid.
        """
        self._gain: float = cordic_gain(n_rotations)
        self._n_rotations: int = int(n_rotations)
        self._n_x: int = int(n_x)
        self._r_x: int = int(r_x)
        self._angle_lut: FixedPointArray = FixedPointArray.from_mantissas(
            _rounded_angle_codes(self._n_rotations),
            ANGLE_WIDTH,
            PHASE_BITS,
        )

    @property
    def n_rotations(self) -> int:
        """Return the number of iterations.

        Returns
        -------
        int
            Iteration count.
        """
        return self._n_rotations

    @property
    def gain(self) -> float:
        """Return the CORDIC gain for this iteration count.

        Returns
        -------
        float
            Gain ``K``.
        """
        return self._gain

    def preload(self, scale: int) -> int:
        """Return the initial x code for ``scale``.

        Parameters
        ----------
        scale : int
            Amplitude scale from 0 to 15. Weight is ``scale / 16``.

        Returns
        -------
        int
            Initial x code. The initial y code is 0.

        Raises
        ------
        ValueError
            If ``scale`` is outside 0 to 15, or this CORDIC is not 16
            iterations of a 16-bit vector.
        """
        if self._n_rotations != 16 or self._n_x != 16:
            raise ValueError(
                "PRELOAD_C is for 16 iterations and a 16-bit vector"
            )
        return scale_preload(PRELOAD_C, scale)

    @property
    def vector_format(self) -> tuple[int, int]:
        """Return the ``(n, r)`` format of ``x`` and ``y``.

        Returns
        -------
        tuple of int
            Signed width and fractional bits of the vector.
        """
        return self._n_x, self._r_x

    def _phase_codes(self, phase: Any) -> np.ndarray:
        """Return phase as integer codes in ``[0, 65535]``.

        Parameters
        ----------
        phase : array-like of int
            Unsigned 16-bit phase codes.

        Returns
        -------
        numpy.ndarray
            Integer codes with the input shape.

        Raises
        ------
        TypeError
            If ``phase`` is not an integer array.
        ValueError
            If any code is outside ``[0, 65535]``.
        """
        codes = np.asarray(phase)
        if codes.dtype == object or not np.issubdtype(codes.dtype, np.integer):
            raise TypeError("phase must be unsigned integer U0.16 codes")
        if np.any(codes < 0) or np.any(codes > 0xFFFF):
            raise ValueError("U0.16 phase codes must be in [0, 65535]")
        return codes

    def _prerotate(
        self,
        x_vector: FixedPointArray,
        y_vector: FixedPointArray,
        quadrant: np.ndarray,
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate ``(x, y)`` by ``quadrant`` quarter-turns.

        Parameters
        ----------
        x_vector : FixedPointArray
            Current x component.
        y_vector : FixedPointArray
            Current y component.
        quadrant : numpy.ndarray
            Quadrant codes 0, 1, 2, or 3, broadcast with the vector.

        Returns
        -------
        tuple of FixedPointArray
            Quadrant 0 keeps ``(x, y)``, 1 returns ``(-y, x)``, 2 returns
            ``(-x, -y)``, and 3 returns ``(y, -x)``.
        """
        x_codes = x_vector.values
        y_codes = y_vector.values
        rotated_x = _quadrant_mux(
            quadrant,
            (x_codes, -y_codes, -x_codes, y_codes),
        )
        rotated_y = _quadrant_mux(
            quadrant,
            (y_codes, x_codes, -y_codes, -x_codes),
        )
        width = max(x_vector.n, y_vector.n, (-x_vector).n, (-y_vector).n)
        return (
            FixedPointArray.from_mantissas(rotated_x, width, x_vector.r),
            FixedPointArray.from_mantissas(rotated_y, width, y_vector.r),
        )

    def _residual_angle(self, offset: np.ndarray) -> FixedPointArray:
        """Return the remaining angle inside the quadrant.

        Parameters
        ----------
        offset : numpy.ndarray
            Low 14 bits of the phase. The remaining angle is in
            ``[0, 1/4)`` of a turn.

        Returns
        -------
        FixedPointArray
            Signed ``(ANGLE_WIDTH, PHASE_BITS)`` codes, with the same
            least significant bit as the phase.
        """
        return FixedPointArray.from_mantissas(
            offset, ANGLE_WIDTH, PHASE_BITS
        )

    def _microrotation(
        self,
        x_vector: FixedPointArray,
        y_vector: FixedPointArray,
        angle: FixedPointArray,
        index: int,
    ) -> tuple[FixedPointArray, FixedPointArray, FixedPointArray]:
        """Apply one CORDIC rotation.

        Parameters
        ----------
        x_vector : FixedPointArray
            Current x component.
        y_vector : FixedPointArray
            Current y component.
        angle : FixedPointArray
            Remaining angle. A negative value reverses the rotation.
        index : int
            Iteration index. ``x`` and ``y`` shift right by this many
            bits.

        Returns
        -------
        tuple of FixedPointArray
            Updated ``(x, y, angle)``.
        """
        # Sign of the remaining angle chooses add or subtract.
        direction = np.where(angle < 0, -1, 1)
        shifted_x = x_vector >> index
        shifted_y = y_vector >> index
        next_x = x_vector - shifted_y * direction
        next_y = y_vector + shifted_x * direction
        step = self._angle_lut[index]
        next_angle = angle - step * direction
        return next_x, next_y, next_angle

    def _rotate_codes(
        self,
        x_codes: np.ndarray,
        y_codes: np.ndarray,
        phase_codes: np.ndarray,
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate integer ``x`` and ``y`` codes by each phase.

        Parameters
        ----------
        x_codes : numpy.ndarray
            Initial x codes, broadcast with ``phase_codes``.
        y_codes : numpy.ndarray
            Initial y codes, broadcast with ``phase_codes``.
        phase_codes : numpy.ndarray
            Unsigned phase codes in ``[0, 65535]``.

        Returns
        -------
        tuple of FixedPointArray
            Rotated ``(x, y)``. The CORDIC gain is included. Codes are
            not saturated.
        """
        x_vector = FixedPointArray.from_mantissas(
            x_codes, self._n_x, self._r_x
        )
        y_vector = FixedPointArray.from_mantissas(
            y_codes, self._n_x, self._r_x
        )
        quadrant = np.asarray(phase_codes >> OFFSET_BITS, dtype=np.int64)
        offset = np.asarray(phase_codes & ((1 << OFFSET_BITS) - 1))
        x_vector, y_vector = self._prerotate(x_vector, y_vector, quadrant)
        angle = self._residual_angle(offset)
        for index in range(self._n_rotations):
            x_vector, y_vector, angle = self._microrotation(
                x_vector, y_vector, angle, index
            )
        return x_vector, y_vector

    def rotate_preload(
        self, scale: int, phase: Any
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate the initial vector for ``scale`` by ``phase``.

        Parameters
        ----------
        scale : int
            Amplitude scale from 0 to 15.
        phase : array-like of int
            Unsigned phase codes in ``[0, 65535]``. ``2**16`` codes is
            one turn.

        Returns
        -------
        tuple of FixedPointArray
            Rotated ``(x, y)`` in the vector format, about ``K`` times
            the initial magnitude times cosine and sine.

        Raises
        ------
        TypeError
            If ``phase`` is not an integer array.
        ValueError
            If ``scale`` or a phase code is out of range, or this
            CORDIC is not 16 iterations of a 16-bit vector.
        """
        phase_codes = np.atleast_1d(self._phase_codes(phase))
        code = self.preload(scale)
        x_codes = np.full(phase_codes.shape, code, dtype=np.int64)
        y_codes = np.zeros(phase_codes.shape, dtype=np.int64)
        return self._rotate_codes(x_codes, y_codes, phase_codes)

    def rotate(
        self, x: Any, y: Any, phase: Any
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate ``(x, y)`` by an unsigned 16-bit phase.

        Parameters
        ----------
        x : array-like of float
            Initial x values, quantized to signed ``(n_x, r_x)``.
        y : array-like of float
            Initial y values, quantized to signed ``(n_x, r_x)``.
        phase : array-like of int
            Unsigned phase codes in ``[0, 65535]``. ``2**16`` codes is
            one turn. The low 14 bits are the remaining angle, in
            ``[0, 1/4)`` of a turn.

        Returns
        -------
        tuple of FixedPointArray
            Rotated ``(x, y)`` in the vector format. The CORDIC gain
            is included.

        Raises
        ------
        TypeError
            If ``phase`` is not an integer array.
        ValueError
            If a phase code is outside ``[0, 65535]``, or if ``x``,
            ``y``, and ``phase`` do not broadcast.
        """
        phase_codes = np.atleast_1d(self._phase_codes(phase))
        try:
            x_real, y_real, phase_codes = np.broadcast_arrays(
                np.asarray(x, dtype=float),
                np.asarray(y, dtype=float),
                phase_codes,
            )
        except ValueError as error:
            raise ValueError(
                "x, y, and phase must be broadcastable"
            ) from error
        x_vector = FixedPointArray(x_real, self._n_x, self._r_x)
        y_vector = FixedPointArray(y_real, self._n_x, self._r_x)
        return self._rotate_codes(
            x_vector.values, y_vector.values, phase_codes
        )


def sweep_and_plot(
    cordic: CORDIC | None = None,
    output_path: str = "cordic.png",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, plt.Figure]:
    """Sweep every phase code and plot cosine with its absolute error.

    Parameters
    ----------
    cordic : CORDIC, optional
        Model to sweep. Default is 16-bit ``x`` and ``y`` with 15
        fractional bits, at amplitude scale 15.
    output_path : str, optional
        Path of the saved figure. Default is ``cordic.png``.

    Returns
    -------
    tuple
        Phase in radians, CORDIC cosine, absolute error, and the
        Matplotlib figure.
    """
    model = CORDIC(r_x=15) if cordic is None else cordic
    phase_codes = np.arange(1 << PHASE_BITS, dtype=np.uint16)
    angles = phase_codes.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
    cosine, _sine = model.rotate_preload(15, phase_codes)
    output = np.reshape(cosine.to_float(), -1)
    preload = model.preload(15) / (1 << model.vector_format[1])
    ideal = preload * model.gain * np.cos(angles)
    absolute_error = np.abs(ideal - output)

    figure, (output_axis, error_axis) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(12, 7),
        gridspec_kw={"height_ratios": [3, 1]},
    )
    output_axis.plot(angles, output, label="Fixed-point CORDIC")
    output_axis.plot(
        angles,
        ideal,
        linestyle="--",
        label="Ideal cos(fixed-point angle)",
    )
    output_axis.set_ylabel("Output value")
    output_axis.legend()
    error_axis.plot(angles, absolute_error)
    error_axis.set_xlabel("Phase angle (radians; input is U0.16 turns)")
    error_axis.set_ylabel("Absolute error")
    error_axis.set_title("CORDIC quantization noise")
    figure.tight_layout()
    figure.savefig(output_path)
    return angles, output, absolute_error, figure


def _code_tolerance(cordic: CORDIC, preload: int) -> float:
    """Return an absolute error bound in vector codes.

    Parameters
    ----------
    cordic : CORDIC
        Model whose iteration count sets the bound.
    preload : int
        Initial x code.

    Returns
    -------
    float
        Allowed absolute error against ``K * preload * cos`` or sine.
    """
    # Half a phase code of angle error per iteration, plus one code
    # per shifted add, each grown by at most K.
    angle_lsb = 2.0 * math.pi / (1 << PHASE_BITS)
    angle_error = 0.5 * cordic.n_rotations * angle_lsb
    shift_error = cordic.n_rotations * cordic.gain
    return abs(preload) * cordic.gain * angle_error + shift_error


class CORDICTests(unittest.TestCase):
    """Tests sine and cosine across all four quadrants."""

    def test_arctangent_table_is_a_binary_angle(self) -> None:
        """Tests that table codes round ``atan(2**-i)`` to U0.16."""
        cordic = CORDIC()
        scale = 1 << PHASE_BITS
        for index, code in enumerate(cordic._angle_lut.values):
            turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            expected = math.floor(turns * scale + 0.5)
            self.assertEqual(int(code), expected)
        self.assertEqual(int(cordic._angle_lut.values[0]), 1 << 13)
        self.assertEqual(int(cordic._angle_lut.values[14]), 1)
        self.assertEqual(int(cordic._angle_lut.values[15]), 0)

    def test_residual_keeps_the_phase_code(self) -> None:
        """Tests that the remaining angle keeps the low 14 phase bits."""
        cordic = CORDIC()
        offset = np.array([0, 1, (1 << OFFSET_BITS) - 1])
        residual = cordic._residual_angle(offset)
        np.testing.assert_array_equal(residual.values, offset)
        self.assertEqual(residual.r, PHASE_BITS)

    def test_gain_is_the_iteration_product(self) -> None:
        """Tests that ``K`` matches :func:`cordic_gain`."""
        cordic = CORDIC()
        self.assertEqual(cordic.gain, cordic_gain(16))
        self.assertGreater(PRELOAD_C, 0)

    def test_preload_is_a_shift_add(self) -> None:
        """Tests the sum of shifted copies of the magnitude constant."""
        cordic = CORDIC()
        self.assertEqual(cordic.preload(0), 0)
        self.assertEqual(cordic.preload(1), PRELOAD_C >> 4)
        self.assertEqual(cordic.preload(8), PRELOAD_C >> 1)
        shifted = (
            (PRELOAD_C >> 1)
            + (PRELOAD_C >> 2)
            + (PRELOAD_C >> 3)
            + (PRELOAD_C >> 4)
        )
        self.assertEqual(cordic.preload(15), shifted)
        # Each shift drops bits that one shift of the product would keep.
        self.assertNotEqual(shifted, (PRELOAD_C * 15) >> 4)
        with self.assertRaises(ValueError):
            cordic.preload(-1)
        with self.assertRaises(ValueError):
            cordic.preload(16)

    def test_axes_match_quadrant_pre_rotation(self) -> None:
        """Tests the four axes, where the remaining angle is zero."""
        cordic = CORDIC(r_x=15)
        phases = np.array([0, 16384, 32768, 49152], dtype=np.uint16)
        cosine, sine = cordic.rotate_preload(15, phases)
        preload = cordic.preload(15)
        tolerance = _code_tolerance(cordic, preload)
        expected_cos = preload * cordic.gain * np.array(
            [1.0, 0.0, -1.0, 0.0]
        )
        expected_sin = preload * cordic.gain * np.array(
            [0.0, 1.0, 0.0, -1.0]
        )
        np.testing.assert_allclose(
            cosine.values.astype(float), expected_cos, atol=tolerance
        )
        np.testing.assert_allclose(
            sine.values.astype(float), expected_sin, atol=tolerance
        )

    def test_scale_15_stays_inside_signed_16_bits(self) -> None:
        """Tests that amplitude scale 15 fits in a signed 16-bit word."""
        cordic = CORDIC(r_x=15)
        phases = np.arange(0, 1 << PHASE_BITS, dtype=np.uint16)
        cosine, sine = cordic.rotate_preload(15, phases)
        low = -(1 << 15)
        high = (1 << 15) - 1
        for codes in (cosine.values, sine.values):
            self.assertGreaterEqual(int(np.min(codes)), low)
            self.assertLessEqual(int(np.max(codes)), high)
        peak = max(
            int(np.max(np.abs(cosine.values))),
            int(np.max(np.abs(sine.values))),
        )
        self.assertEqual(peak, 32766)

    def test_sin_cos_all_quadrants(self) -> None:
        """Tests sine and cosine at every phase code."""
        cordic = CORDIC(r_x=15)
        phases = np.arange(0, 1 << PHASE_BITS, dtype=np.uint16)
        cosine, sine = cordic.rotate_preload(15, phases)
        angles = phases.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
        preload = cordic.preload(15)
        tolerance = _code_tolerance(cordic, preload)
        ideal_cos = preload * cordic.gain * np.cos(angles)
        ideal_sin = preload * cordic.gain * np.sin(angles)
        cos_codes = np.reshape(cosine.values, -1).astype(float)
        sin_codes = np.reshape(sine.values, -1).astype(float)
        np.testing.assert_allclose(cos_codes, ideal_cos, atol=tolerance)
        np.testing.assert_allclose(sin_codes, ideal_sin, atol=tolerance)
        worst = max(
            float(np.max(np.abs(cos_codes - ideal_cos))),
            float(np.max(np.abs(sin_codes - ideal_sin))),
        )
        self.assertAlmostEqual(worst, 12.20, delta=0.05)

    def test_next_constant_leaves_signed_16_bits(self) -> None:
        """Tests that one more than :data:`PRELOAD_C` needs 17 bits."""
        cordic = CORDIC(r_x=15)
        code = scale_preload(PRELOAD_C + 1, 15)
        phases = np.arange(1 << PHASE_BITS, dtype=np.uint16)
        x_codes = np.full(phases.shape, code, dtype=np.int64)
        y_codes = np.zeros(phases.shape, dtype=np.int64)
        cosine, sine = cordic._rotate_codes(x_codes, y_codes, phases)
        peak = max(
            int(np.max(np.abs(cosine.values))),
            int(np.max(np.abs(sine.values))),
        )
        self.assertGreater(peak, (1 << 15) - 1)

    def test_phase_codes_are_rejected_when_out_of_range(self) -> None:
        """Tests rejection of non-integer and out-of-range phase codes."""
        cordic = CORDIC()
        with self.assertRaises(TypeError):
            cordic.rotate_preload(15, 0.5)
        with self.assertRaises(ValueError):
            cordic.rotate_preload(15, -1)
        with self.assertRaises(ValueError):
            cordic.rotate_preload(15, 65536)


def main() -> None:
    """Run the CORDIC tests, then save a full-phase cosine plot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="cordic.png")
    args = parser.parse_args()
    unittest.main(argv=["cordic"], exit=False)
    sweep_and_plot(output_path=args.output)


if __name__ == "__main__":
    main()

"""Rotation-mode CORDIC sine and cosine.

The phase input is an unsigned 16-bit fraction of one turn (U0.16).
``x`` and ``y`` are returned in the signed fixed-point format passed
to the constructor.
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
# Starting magnitude that makes scale 15 a full-scale output
# (about 2**15 / K * 16/15).
FULL_SCALE_CONSTANT = 21223


def calculate_cordic_gain(n_rotations: int) -> float:
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


def calculate_initial_magnitude(
    full_scale_constant: int, scale: int
) -> int:
    """Return the initial x integer for a 4-bit amplitude scale.

    Scale 15 is full scale. The rotation output is about
    ``scale / 15`` of full scale.

    Parameters
    ----------
    full_scale_constant : int
        Starting magnitude for scale 15, in the same integer units as
        ``x``. Chosen so scale 15 is full scale. About
        ``2**15 / K * 16 / 15`` for a 16-bit vector.
    scale : int
        Amplitude scale from 0 to 15. Scale 15 is full scale.

    Returns
    -------
    int
        Initial x integer.

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
            total += int(full_scale_constant) >> (SCALE_BITS - bit)
    return total


def _calculate_arctangent_table(n_rotations: int) -> list[int]:
    """Return arctangent table integers as fractions of a turn.

    Parameters
    ----------
    n_rotations : int
        Number of entries, one per iteration.

    Returns
    -------
    list of int
        Entry ``i`` is ``atan(2**(-i)) / (2*pi)`` rounded to the
        nearest U0.16 integer.
    """
    one_turn = 1 << PHASE_BITS
    table = []
    for index in range(n_rotations):
        turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
        # Round half up. These values are positive.
        table.append(int(math.floor(turns * one_turn + 0.5)))
    return table


def _select_vector_for_quadrant(
    quadrant: np.ndarray,
    rotated_vectors: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    """Select the x or y integers for each quadrant.

    Parameters
    ----------
    quadrant : numpy.ndarray
        Quadrant index, 0, 1, 2, or 3.
    rotated_vectors : tuple of numpy.ndarray
        Four arrays, one for each quadrant, broadcastable with
        ``quadrant``.

    Returns
    -------
    numpy.ndarray
        ``rotated_vectors[quadrant]`` at each element.
    """
    selected = rotated_vectors[0]
    for index in range(1, 4):
        selected = np.where(
            quadrant == index, rotated_vectors[index], selected
        )
    return selected


class CORDIC:
    """Rotation-mode CORDIC.

    The phase input is an unsigned 16-bit fraction of one turn (U0.16).
    ``x`` and ``y`` use the signed fixed-point format ``(n_x, r_x)``
    passed to the constructor.
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
            Fractional bits of ``x`` and ``y``. Default is 13, leaving
            integer headroom for the CORDIC gain.

        Raises
        ------
        ValueError
            If an iteration count or format is not valid.
        """
        self._gain: float = calculate_cordic_gain(n_rotations)
        self._n_rotations: int = int(n_rotations)
        self._n_x: int = int(n_x)
        self._r_x: int = int(r_x)
        self._angle_lut: FixedPointArray = FixedPointArray.from_mantissas(
            _calculate_arctangent_table(self._n_rotations),
            ANGLE_WIDTH,
            PHASE_BITS,
        )

    def get_n_rotations(self) -> int:
        """Return the number of iterations.

        Returns
        -------
        int
            Iteration count.
        """
        return self._n_rotations

    def get_gain(self) -> float:
        """Return the CORDIC gain for this iteration count.

        Returns
        -------
        float
            Gain ``K``.
        """
        return self._gain

    def get_initial_magnitude(self, scale: int) -> int:
        """Return the initial x integer for ``scale``.

        Scale 15 is full scale. The rotation output is about
        ``scale / 15`` of full scale.

        Parameters
        ----------
        scale : int
            Amplitude scale from 0 to 15. Scale 15 is full scale.

        Returns
        -------
        int
            Initial x integer. The initial y integer is 0.

        Raises
        ------
        ValueError
            If ``scale`` is outside 0 to 15, or this CORDIC is not 16
            iterations of a 16-bit vector.
        """
        if self._n_rotations != 16 or self._n_x != 16:
            raise ValueError(
                "FULL_SCALE_CONSTANT is for 16 iterations and a 16-bit vector"
            )
        return calculate_initial_magnitude(FULL_SCALE_CONSTANT, scale)

    def get_vector_format(self) -> tuple[int, int]:
        """Return the ``(n, r)`` format of ``x`` and ``y``.

        Returns
        -------
        tuple of int
            Signed width and fractional bits of the vector.
        """
        return self._n_x, self._r_x

    def _convert_phase_to_integers(self, phase: Any) -> np.ndarray:
        """Return phase integers, rejecting values outside ``[0, 65535]``.

        Parameters
        ----------
        phase : array-like of int
            Unsigned 16-bit phase.

        Returns
        -------
        numpy.ndarray
            Integer phase values with the input shape.

        Raises
        ------
        TypeError
            If ``phase`` is not an integer array.
        ValueError
            If any value is outside ``[0, 65535]``.
        """
        phase_integers = np.asarray(phase)
        if (
            phase_integers.dtype == object
            or not np.issubdtype(phase_integers.dtype, np.integer)
        ):
            raise TypeError("phase must be unsigned U0.16 integers")
        if np.any(phase_integers < 0) or np.any(phase_integers > 0xFFFF):
            raise ValueError("U0.16 phase integers must be in [0, 65535]")
        return phase_integers

    def _apply_quadrant_rotation(
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
            Quadrant index, 0, 1, 2, or 3, broadcast with the vector.

        Returns
        -------
        tuple of FixedPointArray
            Quadrant 0 keeps ``(x, y)``, 1 returns ``(-y, x)``, 2 returns
            ``(-x, -y)``, and 3 returns ``(y, -x)``.
        """
        x_integers = x_vector.values
        y_integers = y_vector.values
        rotated_x = _select_vector_for_quadrant(
            quadrant,
            (x_integers, -y_integers, -x_integers, y_integers),
        )
        rotated_y = _select_vector_for_quadrant(
            quadrant,
            (y_integers, x_integers, -y_integers, -x_integers),
        )
        width = max(x_vector.n, y_vector.n, (-x_vector).n, (-y_vector).n)
        return (
            FixedPointArray.from_mantissas(rotated_x, width, x_vector.r),
            FixedPointArray.from_mantissas(rotated_y, width, y_vector.r),
        )

    def _calculate_remaining_angle(
        self, offset: np.ndarray
    ) -> FixedPointArray:
        """Return the remaining angle inside the quadrant.

        Parameters
        ----------
        offset : numpy.ndarray
            Low 14 bits of the phase. The remaining angle is in
            ``[0, 1/4)`` of a turn.

        Returns
        -------
        FixedPointArray
            Signed ``(ANGLE_WIDTH, PHASE_BITS)`` integers, with the
            same least significant bit as the phase.
        """
        return FixedPointArray.from_mantissas(
            offset, ANGLE_WIDTH, PHASE_BITS
        )

    def _apply_rotation_step(
        self,
        x_vector: FixedPointArray,
        y_vector: FixedPointArray,
        angle: FixedPointArray,
        index: int,
    ) -> tuple[FixedPointArray, FixedPointArray, FixedPointArray]:
        """Apply one CORDIC rotation step.

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

    def _rotate_integers(
        self,
        x_integers: np.ndarray,
        y_integers: np.ndarray,
        phase_integers: np.ndarray,
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate integer ``x`` and ``y`` values by each phase.

        Parameters
        ----------
        x_integers : numpy.ndarray
            Initial x integers, broadcast with ``phase_integers``.
        y_integers : numpy.ndarray
            Initial y integers, broadcast with ``phase_integers``.
        phase_integers : numpy.ndarray
            Unsigned phase integers in ``[0, 65535]``.

        Returns
        -------
        tuple of FixedPointArray
            Rotated ``(x, y)``. The CORDIC gain is included. Results
            are not saturated.
        """
        x_vector = FixedPointArray.from_mantissas(
            x_integers, self._n_x, self._r_x
        )
        y_vector = FixedPointArray.from_mantissas(
            y_integers, self._n_x, self._r_x
        )
        quadrant = np.asarray(phase_integers >> OFFSET_BITS, dtype=np.int64)
        offset = np.asarray(phase_integers & ((1 << OFFSET_BITS) - 1))
        x_vector, y_vector = self._apply_quadrant_rotation(
            x_vector, y_vector, quadrant
        )
        angle = self._calculate_remaining_angle(offset)
        for index in range(self._n_rotations):
            x_vector, y_vector, angle = self._apply_rotation_step(
                x_vector, y_vector, angle, index
            )
        return x_vector, y_vector

    def rotate_initial_vector(
        self, scale: int, phase: Any
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate the initial vector for ``scale`` by ``phase``.

        Parameters
        ----------
        scale : int
            Amplitude scale from 0 to 15. Scale 15 is full scale.
        phase : array-like of int
            Unsigned phase integers in ``[0, 65535]``. ``2**16`` is
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
            If ``scale`` or a phase integer is out of range, or this
            CORDIC is not 16 iterations of a 16-bit vector.
        """
        phase_integers = np.atleast_1d(self._convert_phase_to_integers(phase))
        initial = self.get_initial_magnitude(scale)
        x_integers = np.full(phase_integers.shape, initial, dtype=np.int64)
        y_integers = np.zeros(phase_integers.shape, dtype=np.int64)
        return self._rotate_integers(x_integers, y_integers, phase_integers)

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
            Unsigned phase integers in ``[0, 65535]``. ``2**16`` is
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
            If a phase integer is outside ``[0, 65535]``, or if ``x``,
            ``y``, and ``phase`` do not broadcast.
        """
        phase_integers = np.atleast_1d(self._convert_phase_to_integers(phase))
        try:
            x_real, y_real, phase_integers = np.broadcast_arrays(
                np.asarray(x, dtype=float),
                np.asarray(y, dtype=float),
                phase_integers,
            )
        except ValueError as error:
            raise ValueError(
                "x, y, and phase must be broadcastable"
            ) from error
        x_vector = FixedPointArray(x_real, self._n_x, self._r_x)
        y_vector = FixedPointArray(y_real, self._n_x, self._r_x)
        return self._rotate_integers(
            x_vector.values, y_vector.values, phase_integers
        )


def sweep_and_plot(
    cordic: CORDIC | None = None,
    output_path: str = "cordic.png",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, plt.Figure]:
    """Sweep every phase and plot cosine with its absolute error.

    Parameters
    ----------
    cordic : CORDIC, optional
        Model to sweep. When omitted, ``x`` and ``y`` are 16 bits
        with 15 fractional bits, so full scale is just under 1, at
        amplitude scale 15.
    output_path : str, optional
        Path of the saved figure. Default is ``cordic.png``.

    Returns
    -------
    tuple
        Phase in radians, CORDIC cosine, absolute error, and the
        Matplotlib figure.
    """
    model = CORDIC(r_x=15) if cordic is None else cordic
    phase_integers = np.arange(1 << PHASE_BITS, dtype=np.uint16)
    angles = phase_integers.astype(float) * (
        2.0 * math.pi / (1 << PHASE_BITS)
    )
    cosine, _sine = model.rotate_initial_vector(15, phase_integers)
    output = np.reshape(cosine.to_float(), -1)
    fraction = model.get_vector_format()[1]
    initial_magnitude = model.get_initial_magnitude(15) / (1 << fraction)
    ideal = initial_magnitude * model.get_gain() * np.cos(angles)
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


def _calculate_error_tolerance_lsb(
    cordic: CORDIC, initial_magnitude: int
) -> float:
    """Return an absolute error bound in LSBs of ``x`` and ``y``.

    Parameters
    ----------
    cordic : CORDIC
        Model whose iteration count sets the bound.
    initial_magnitude : int
        Initial x integer.

    Returns
    -------
    float
        Allowed absolute error against ``K * initial_magnitude * cos``
        or sine, in LSBs.
    """
    # Half an LSB of angle error per iteration, plus one LSB per
    # shifted add, each grown by at most K.
    angle_lsb = 2.0 * math.pi / (1 << PHASE_BITS)
    angle_error = 0.5 * cordic.get_n_rotations() * angle_lsb
    shift_error = cordic.get_n_rotations() * cordic.get_gain()
    return (
        abs(initial_magnitude) * cordic.get_gain() * angle_error
        + shift_error
    )


class CORDICTests(unittest.TestCase):
    """Tests sine and cosine across all four quadrants."""

    def test_arctangent_table_is_a_binary_angle(self) -> None:
        """Tests that table integers round ``atan(2**-i)`` to U0.16."""
        cordic = CORDIC()
        one_turn = 1 << PHASE_BITS
        for index, entry in enumerate(cordic._angle_lut.values):
            turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            expected = math.floor(turns * one_turn + 0.5)
            self.assertEqual(int(entry), expected)
        self.assertEqual(int(cordic._angle_lut.values[0]), 1 << 13)
        self.assertEqual(int(cordic._angle_lut.values[14]), 1)
        self.assertEqual(int(cordic._angle_lut.values[15]), 0)

    def test_remaining_angle_keeps_the_phase_integer(self) -> None:
        """Tests that the remaining angle keeps the low 14 phase bits."""
        cordic = CORDIC()
        offset = np.array([0, 1, (1 << OFFSET_BITS) - 1])
        remaining = cordic._calculate_remaining_angle(offset)
        np.testing.assert_array_equal(remaining.values, offset)
        self.assertEqual(remaining.r, PHASE_BITS)

    def test_gain_is_the_iteration_product(self) -> None:
        """Tests that ``K`` matches :func:`calculate_cordic_gain`."""
        cordic = CORDIC()
        self.assertEqual(cordic.get_gain(), calculate_cordic_gain(16))
        self.assertGreater(FULL_SCALE_CONSTANT, 0)

    def test_initial_magnitude_is_a_sum_of_shifts(self) -> None:
        """Tests the sum of shifted copies of the magnitude constant."""
        cordic = CORDIC()
        self.assertEqual(cordic.get_initial_magnitude(0), 0)
        self.assertEqual(
            cordic.get_initial_magnitude(1), FULL_SCALE_CONSTANT >> 4
        )
        self.assertEqual(
            cordic.get_initial_magnitude(8), FULL_SCALE_CONSTANT >> 1
        )
        shifted = (
            (FULL_SCALE_CONSTANT >> 1)
            + (FULL_SCALE_CONSTANT >> 2)
            + (FULL_SCALE_CONSTANT >> 3)
            + (FULL_SCALE_CONSTANT >> 4)
        )
        self.assertEqual(cordic.get_initial_magnitude(15), shifted)
        # Each shift drops bits that one shift of the product would keep.
        self.assertNotEqual(shifted, (FULL_SCALE_CONSTANT * 15) >> 4)
        with self.assertRaises(ValueError):
            cordic.get_initial_magnitude(-1)
        with self.assertRaises(ValueError):
            cordic.get_initial_magnitude(16)

    def test_axes_match_quadrant_rotation(self) -> None:
        """Tests the four axes, where the remaining angle is zero."""
        cordic = CORDIC(r_x=15)
        phases = np.array([0, 16384, 32768, 49152], dtype=np.uint16)
        cosine, sine = cordic.rotate_initial_vector(15, phases)
        initial = cordic.get_initial_magnitude(15)
        tolerance = _calculate_error_tolerance_lsb(cordic, initial)
        expected_cos = initial * cordic.get_gain() * np.array(
            [1.0, 0.0, -1.0, 0.0]
        )
        expected_sin = initial * cordic.get_gain() * np.array(
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
        cosine, sine = cordic.rotate_initial_vector(15, phases)
        low = -(1 << 15)
        high = (1 << 15) - 1
        for values in (cosine.values, sine.values):
            self.assertGreaterEqual(int(np.min(values)), low)
            self.assertLessEqual(int(np.max(values)), high)
        peak = max(
            int(np.max(np.abs(cosine.values))),
            int(np.max(np.abs(sine.values))),
        )
        self.assertEqual(peak, 32766)

    def test_sin_cos_all_quadrants(self) -> None:
        """Tests sine and cosine at every phase."""
        cordic = CORDIC(r_x=15)
        phases = np.arange(0, 1 << PHASE_BITS, dtype=np.uint16)
        cosine, sine = cordic.rotate_initial_vector(15, phases)
        angles = phases.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
        initial = cordic.get_initial_magnitude(15)
        tolerance = _calculate_error_tolerance_lsb(cordic, initial)
        ideal_cos = initial * cordic.get_gain() * np.cos(angles)
        ideal_sin = initial * cordic.get_gain() * np.sin(angles)
        cos_values = np.reshape(cosine.values, -1).astype(float)
        sin_values = np.reshape(sine.values, -1).astype(float)
        np.testing.assert_allclose(cos_values, ideal_cos, atol=tolerance)
        np.testing.assert_allclose(sin_values, ideal_sin, atol=tolerance)
        worst = max(
            float(np.max(np.abs(cos_values - ideal_cos))),
            float(np.max(np.abs(sin_values - ideal_sin))),
        )
        self.assertAlmostEqual(worst, 12.20, delta=0.05)

    def test_next_constant_leaves_signed_16_bits(self) -> None:
        """Tests that one more than ``FULL_SCALE_CONSTANT`` needs 17 bits."""
        cordic = CORDIC(r_x=15)
        initial = calculate_initial_magnitude(FULL_SCALE_CONSTANT + 1, 15)
        phases = np.arange(1 << PHASE_BITS, dtype=np.uint16)
        x_integers = np.full(phases.shape, initial, dtype=np.int64)
        y_integers = np.zeros(phases.shape, dtype=np.int64)
        cosine, sine = cordic._rotate_integers(
            x_integers, y_integers, phases
        )
        peak = max(
            int(np.max(np.abs(cosine.values))),
            int(np.max(np.abs(sine.values))),
        )
        self.assertGreater(peak, (1 << 15) - 1)

    def test_out_of_range_phase_is_rejected(self) -> None:
        """Tests rejection of non-integer and out-of-range phase values."""
        cordic = CORDIC()
        with self.assertRaises(TypeError):
            cordic.rotate_initial_vector(15, 0.5)
        with self.assertRaises(ValueError):
            cordic.rotate_initial_vector(15, -1)
        with self.assertRaises(ValueError):
            cordic.rotate_initial_vector(15, 65536)


def main() -> None:
    """Run the CORDIC tests, then save a full-phase cosine plot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="cordic.png")
    args = parser.parse_args()
    unittest.main(argv=["cordic"], exit=False)
    sweep_and_plot(output_path=args.output)


if __name__ == "__main__":
    main()

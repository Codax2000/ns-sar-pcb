"""Rotation-mode CORDIC cosine.

Sixteen iterations. ``x`` and ``y`` are signed 16-bit values with 15
fractional bits. ``cordic_rotate`` takes a 4-bit amplitude scale and a
phase in signed format ``(16, 16)``, and returns the cosine.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

from fp_array import FixedPointArray


PHASE_BITS = 16
_ITERATIONS = 16
_VECTOR_BITS = 16
_VECTOR_FRACTION = 15
_QUADRANT_SHIFT = 14
_SCALE_BITS = 4
_SCALE_MAX = (1 << _SCALE_BITS) - 1
# Signed (16, 16): the same 16-bit pattern as the U0.16 phase register.
_ANGLE_QUANTIZATION = (PHASE_BITS, PHASE_BITS)
# Starting magnitude constant so scale 15 is full scale
# (about 2**15 / K * 16/15).
FULL_SCALE_CONSTANT = 21223
# atan(2**(-i)) / (2*pi), rounded half up into U0.16.
_arctangent_integers = []
for _index in range(_ITERATIONS):
    _turns = math.atan(2.0 ** (-_index)) / (2.0 * math.pi)
    _arctangent_integers.append(
        int(math.floor(_turns * (1 << PHASE_BITS) + 0.5))
    )
_ARCTANGENT_TABLE = FixedPointArray.from_mantissas(
    _arctangent_integers, _ANGLE_QUANTIZATION[0], _ANGLE_QUANTIZATION[1]
)
# Product of sqrt(1 + 2**(-2*i)) over the 16 iterations.
_gain = 1.0
for _index in range(_ITERATIONS):
    _gain *= math.sqrt(1.0 + 2.0 ** (-2 * _index))
CORDIC_GAIN = _gain


def cordic_rotate(
    magnitudes: int | np.ndarray, angles: FixedPointArray
) -> FixedPointArray:
    """Return about ``magnitudes / 15`` of full scale times cosine.

    ``magnitudes`` is the raw 4-bit amplitude scale register value,
    from 0 to 15. Pass a Python ``int`` or an unsigned-integer NumPy
    array. The starting ``x`` is the right-shift-and-add of
    ``FULL_SCALE_CONSTANT``. That constant absorbs the CORDIC gain, so
    the cosine has no extra factor of ``K``.

    ``angles`` uses quantization ``(16, 16)``: 16 bits, all fractional,
    the same 16-bit pattern as the U0.16 phase register. Fixed-point
    values are signed, so the stored value reads as ``[-1/2, 1/2)`` of
    a turn. That is the same angle modulo one turn. The quadrant is the
    top two bits of the 16-bit pattern.

    Parameters
    ----------
    magnitudes : int or numpy.ndarray
        Amplitude scale, 0 to 15. An array must have an unsigned integer
        dtype and must broadcast to ``angles`` without changing that
        shape.
    angles : FixedPointArray
        Phase, quantization ``(16, 16)``.

    Returns
    -------
    FixedPointArray
        Cosine, about ``magnitudes / 15`` of full scale, in the ``x``
        format.

    Raises
    ------
    TypeError
        If ``magnitudes`` is not an int or a NumPy array, if that
        array is not an unsigned integer dtype, or if ``angles`` is
        not a FixedPointArray. The message names the type or dtype.
    ValueError
        If a scale is outside 0 to 15, the shapes cannot broadcast,
        broadcasting would change the angle shape, or the angle
        quantization is not ``(16, 16)``. The message names the values
        or shapes.
    """
    if isinstance(magnitudes, bool) or not (
        isinstance(magnitudes, int) or isinstance(magnitudes, np.ndarray)
    ):
        received = type(magnitudes).__name__
        raise TypeError(
            "magnitudes must be an int or a numpy array, "
            f"got {received}"
        )
    if isinstance(magnitudes, np.ndarray) and not np.issubdtype(
        magnitudes.dtype, np.unsignedinteger
    ):
        raise TypeError(
            "magnitudes must have an unsigned integer dtype, "
            f"got {magnitudes.dtype}"
        )
    if isinstance(magnitudes, np.ndarray):
        if magnitudes.size:
            found_min = int(np.min(magnitudes))
            found_max = int(np.max(magnitudes))
            if found_min < 0 or found_max > _SCALE_MAX:
                raise ValueError(
                    "magnitudes must be between 0 and 15, "
                    f"got min {found_min} and max {found_max}"
                )
    elif magnitudes < 0 or magnitudes > _SCALE_MAX:
        raise ValueError(
            "magnitudes must be between 0 and 15, "
            f"got min {magnitudes} and max {magnitudes}"
        )
    if not isinstance(angles, FixedPointArray):
        raise TypeError(
            "angles must be a FixedPointArray, "
            f"got {type(angles).__name__}"
        )
    quantization = angles.get_quantization()
    if quantization != _ANGLE_QUANTIZATION:
        raise ValueError(
            "angles quantization must be (16, 16), "
            f"got {quantization}"
        )
    angle_shape = angles.get_mantissas().shape
    magnitude_shape = np.shape(magnitudes)
    try:
        broadcast_shape = np.broadcast_shapes(
            magnitude_shape, angle_shape
        )
    except ValueError as error:
        raise ValueError(
            f"magnitudes shape {magnitude_shape} cannot broadcast "
            f"to angles shape {angle_shape}"
        ) from error
    if broadcast_shape != angle_shape:
        raise ValueError(
            f"magnitudes shape {magnitude_shape} broadcasts to "
            f"{broadcast_shape}, which changes angles shape "
            f"{angle_shape}"
        )
    scales = np.broadcast_to(
        np.asarray(magnitudes, dtype=np.int64), angle_shape
    )
    magnitude = _get_initial_vector(scales)
    remaining_angles, x_vector, y_vector = _pre_rotate(angles, magnitude)
    for index in range(_ITERATIONS):
        directions = _calculate_directions(remaining_angles)
        shifted_x = x_vector >> index
        shifted_y = y_vector >> index
        x_vector = x_vector - shifted_y * directions
        y_vector = y_vector + shifted_x * directions
        # +1 when the remaining angle is >= 0, so the arctangent
        # is subtracted.
        remaining_angles = (
            remaining_angles - _ARCTANGENT_TABLE[index] * directions
        )
    return x_vector


def _get_initial_vector(scales: np.ndarray) -> np.ndarray:
    """Return the starting ``x`` integer for each amplitude scale.

    Bit ``i`` (0 is the least significant bit) adds
    ``FULL_SCALE_CONSTANT >> (4 - i)``. The shift truncates toward
    negative infinity.

    Parameters
    ----------
    scales : numpy.ndarray
        Amplitude scale integers, 0 to 15.

    Returns
    -------
    numpy.ndarray
        Starting ``x`` integers, ``int64``.
    """
    total = np.zeros(scales.shape, dtype=np.int64)
    for bit in range(_SCALE_BITS):
        # Bit 0 is the LSB. The shift truncates toward -infinity.
        shifted = FULL_SCALE_CONSTANT >> (_SCALE_BITS - bit)
        total = total + ((scales >> bit) & 1) * shifted
    return total


def _pre_rotate(
    angles: FixedPointArray, magnitude: np.ndarray
) -> tuple[FixedPointArray, FixedPointArray, FixedPointArray]:
    """Place the magnitude on an axis and return the remaining angle.

    ``y`` starts at 0. Quadrant 0 returns ``(magnitude, 0)``, 1 returns
    ``(0, magnitude)``, 2 returns ``(-magnitude, 0)``, and 3 returns
    ``(0, -magnitude)``.

    Parameters
    ----------
    angles : FixedPointArray
        Phase in quantization ``(16, 16)``.
    magnitude : numpy.ndarray
        Starting x integers.

    Returns
    -------
    tuple of FixedPointArray
        Remaining angle, then ``x`` and ``y`` on the quadrant axis.
    """
    phase = np.asarray(angles.get_mantissas(), dtype=np.int64)
    # Quadrant is the top two bits of the 16-bit pattern. Mask first
    # because the stored value is a signed reading of those bits.
    pattern = phase & ((1 << PHASE_BITS) - 1)
    quadrant = pattern >> _QUADRANT_SHIFT
    offset = pattern & ((1 << _QUADRANT_SHIFT) - 1)
    # Remaining angle is in [0, 1/4) of a turn. Signed (16, 16),
    # the same least significant bit as the phase.
    remaining_angles = FixedPointArray.from_mantissas(
        offset, _ANGLE_QUANTIZATION[0], _ANGLE_QUANTIZATION[1]
    )
    zeros = np.zeros(magnitude.shape, dtype=np.int64)
    x_for_quadrant = (magnitude, zeros, -magnitude, zeros)
    y_for_quadrant = (zeros, magnitude, zeros, -magnitude)
    rotated_x = x_for_quadrant[0]
    rotated_y = y_for_quadrant[0]
    for quadrant_index in range(1, 4):
        rotated_x = np.where(
            quadrant == quadrant_index,
            x_for_quadrant[quadrant_index],
            rotated_x,
        )
        rotated_y = np.where(
            quadrant == quadrant_index,
            y_for_quadrant[quadrant_index],
            rotated_y,
        )
    return (
        remaining_angles,
        FixedPointArray.from_mantissas(
            rotated_x, _VECTOR_BITS, _VECTOR_FRACTION
        ),
        FixedPointArray.from_mantissas(
            rotated_y, _VECTOR_BITS, _VECTOR_FRACTION
        ),
    )


def _calculate_directions(remaining_angles: FixedPointArray) -> np.ndarray:
    """Return +1 or -1 from the sign of the remaining angle.

    Parameters
    ----------
    remaining_angles : FixedPointArray
        Angle still to rotate.

    Returns
    -------
    numpy.ndarray
        +1 when the remaining angle is non-negative, otherwise -1.
    """
    return np.where(remaining_angles < 0, -1, 1)


class CORDICTests(unittest.TestCase):
    """Tests cosine across all four quadrants."""

    def _angles(self, phase: np.ndarray) -> FixedPointArray:
        """Return ``phase`` as signed ``(16, 16)`` with the same bits.

        Parameters
        ----------
        phase : numpy.ndarray
            Unsigned phase integers, 0 to 65535.

        Returns
        -------
        FixedPointArray
            Quantization ``(16, 16)``. Values at or above half a turn
            read as negative.
        """
        unsigned = np.asarray(phase, dtype=np.uint16)
        signed = unsigned.astype(np.int16).astype(np.int64)
        width, fraction = _ANGLE_QUANTIZATION
        return FixedPointArray.from_mantissas(signed, width, fraction)

    def _cosine_tolerance(self, magnitude: int) -> float:
        """Return the absolute cosine tolerance used by the tests.

        Parameters
        ----------
        magnitude : int
            Starting x integer.

        Returns
        -------
        float
            Allowed absolute error, in the same integers as ``x``.
        """
        # Half an LSB of angle error per iteration, plus one LSB per
        # shifted add, each grown by at most K.
        angle_lsb = 2.0 * math.pi / (1 << PHASE_BITS)
        angle_error = 0.5 * _ITERATIONS * angle_lsb
        shift_error = _ITERATIONS * CORDIC_GAIN
        return abs(magnitude) * CORDIC_GAIN * angle_error + shift_error

    def test_arctangent_table_is_a_binary_angle(self) -> None:
        """Tests that table integers round ``atan(2**-i)`` to U0.16."""
        one_turn = 1 << PHASE_BITS
        mantissas = _ARCTANGENT_TABLE.get_mantissas()
        for index, entry in enumerate(mantissas):
            turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            expected = math.floor(turns * one_turn + 0.5)
            self.assertEqual(int(entry), expected)
        self.assertEqual(int(mantissas[0]), 1 << 13)
        self.assertEqual(int(mantissas[14]), 1)
        self.assertEqual(int(mantissas[15]), 0)

    def test_initial_magnitude_is_a_sum_of_shifts(self) -> None:
        """Tests the sum of shifted copies of the magnitude constant."""
        scales = np.array([0, 1, 8, 15], dtype=np.int64)
        initial = _get_initial_vector(scales)
        self.assertEqual(int(initial[0]), 0)
        self.assertEqual(int(initial[1]), FULL_SCALE_CONSTANT >> 4)
        self.assertEqual(int(initial[2]), FULL_SCALE_CONSTANT >> 1)
        shifted = (
            (FULL_SCALE_CONSTANT >> 1)
            + (FULL_SCALE_CONSTANT >> 2)
            + (FULL_SCALE_CONSTANT >> 3)
            + (FULL_SCALE_CONSTANT >> 4)
        )
        self.assertEqual(int(initial[3]), shifted)
        self.assertEqual(shifted, 19894)
        # Each shift drops bits that one shift of the product would keep.
        self.assertNotEqual(shifted, (FULL_SCALE_CONSTANT * 15) >> 4)

    def test_remaining_angle_keeps_the_low_phase_bits(self) -> None:
        """Tests that the remaining angle keeps the low 14 phase bits."""
        phase = np.array(
            [0, 1, (1 << _QUADRANT_SHIFT) - 1, 16384 + 5, 32768 + 7, 65535]
        )
        angles = self._angles(phase)
        scales = np.full(phase.shape, 1, dtype=np.int64)
        magnitude = _get_initial_vector(scales)
        remaining, _x_vector, _y_vector = _pre_rotate(angles, magnitude)
        low_bits = (1 << _QUADRANT_SHIFT) - 1
        np.testing.assert_array_equal(
            remaining.get_mantissas(),
            [0, 1, low_bits, 5, 7, low_bits],
        )
        self.assertEqual(remaining.get_quantization(), _ANGLE_QUANTIZATION)

    def test_axes_match_quadrant_rotation(self) -> None:
        """Tests the four axes, where the remaining angle is zero."""
        phases = np.array([0, 16384, 32768, 49152], dtype=np.uint16)
        angles = self._angles(phases)
        scales = np.full(phases.shape, 15, dtype=np.uint8)
        cosine = cordic_rotate(scales, angles)
        initial = int(_get_initial_vector(np.array([15]))[0])
        expected = initial * CORDIC_GAIN * np.array([1.0, 0.0, -1.0, 0.0])
        np.testing.assert_allclose(
            cosine.get_mantissas().astype(float),
            expected,
            atol=self._cosine_tolerance(initial),
        )

    def test_scale_15_stays_inside_signed_16_bits(self) -> None:
        """Tests that amplitude scale 15 fits in a signed 16-bit word."""
        phases = np.arange(1 << PHASE_BITS, dtype=np.uint16)
        cosine = cordic_rotate(15, self._angles(phases))
        values = cosine.get_mantissas()
        self.assertGreaterEqual(int(np.min(values)), -(1 << 15))
        self.assertLessEqual(int(np.max(values)), (1 << 15) - 1)
        self.assertEqual(int(np.max(np.abs(values))), 32766)

    def test_cosine_at_every_phase(self) -> None:
        """Tests cosine at every phase for amplitude scale 15."""
        phases = np.arange(1 << PHASE_BITS, dtype=np.uint16)
        cosine = cordic_rotate(15, self._angles(phases))
        turns = phases.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
        initial = int(_get_initial_vector(np.array([15]))[0])
        ideal = initial * CORDIC_GAIN * np.cos(turns)
        values = np.reshape(cosine.get_mantissas(), -1).astype(float)
        np.testing.assert_allclose(
            values, ideal, atol=self._cosine_tolerance(initial)
        )
        worst = float(np.max(np.abs(values - ideal)))
        self.assertAlmostEqual(worst, 12.20, delta=0.05)

    def test_scale_array_broadcasts_to_the_angles(self) -> None:
        """Tests that a length-1 unsigned scale matches a scalar scale."""
        phases = np.array([0, 16384, 32768, 49152], dtype=np.uint16)
        angles = self._angles(phases)
        scalar = cordic_rotate(15, angles)
        array = cordic_rotate(np.array([15], dtype=np.uint8), angles)
        np.testing.assert_array_equal(
            scalar.get_mantissas(), array.get_mantissas()
        )

    def test_rejects_a_magnitude_that_is_not_an_array(self) -> None:
        """Tests that a non-int, non-array magnitude names its type."""
        angles = self._angles(np.array([0]))
        with self.assertRaises(TypeError) as caught:
            cordic_rotate([15], angles)
        self.assertIn("list", str(caught.exception))
        with self.assertRaises(TypeError) as caught:
            cordic_rotate(True, angles)
        self.assertIn("bool", str(caught.exception))
        with self.assertRaises(TypeError) as caught:
            cordic_rotate(np.uint8(1), angles)
        self.assertIn("uint8", str(caught.exception))

    def test_rejects_a_signed_magnitude_array(self) -> None:
        """Tests that a signed magnitude array names its dtype."""
        angles = self._angles(np.array([0]))
        scales = np.array([1], dtype=np.int64)
        with self.assertRaises(TypeError) as caught:
            cordic_rotate(scales, angles)
        self.assertIn("int64", str(caught.exception))

    def test_rejects_a_magnitude_outside_0_to_15(self) -> None:
        """Tests that an out-of-range scale names the min and max."""
        angles = self._angles(np.array([0, 1]))
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(16, angles)
        self.assertIn("min 16", str(caught.exception))
        self.assertIn("max 16", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(-1, angles)
        self.assertIn("min -1", str(caught.exception))
        self.assertIn("max -1", str(caught.exception))
        scales = np.array([0, 20], dtype=np.uint8)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(scales, angles)
        self.assertIn("min 0", str(caught.exception))
        self.assertIn("max 20", str(caught.exception))

    def test_rejects_a_magnitude_that_cannot_broadcast(self) -> None:
        """Tests that incompatible shapes are both named."""
        angles = self._angles(np.zeros(4, dtype=np.uint16))
        scales = np.zeros(3, dtype=np.uint8)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(scales, angles)
        message = str(caught.exception)
        self.assertIn("(3,)", message)
        self.assertIn("(4,)", message)

    def test_rejects_a_magnitude_that_changes_the_angle_shape(self) -> None:
        """Tests that a shape-changing broadcast names all three shapes."""
        angles = self._angles(np.zeros(4, dtype=np.uint16))
        scales = np.zeros((4, 1), dtype=np.uint8)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(scales, angles)
        message = str(caught.exception)
        self.assertIn("(4, 1)", message)
        self.assertIn("(4,)", message)
        self.assertIn("(4, 4)", message)

    def test_rejects_an_angle_that_is_not_fixed_point(self) -> None:
        """Tests that a non-fixed-point phase names its type."""
        with self.assertRaises(TypeError) as caught:
            cordic_rotate(1, np.array([0]))
        self.assertIn("ndarray", str(caught.exception))

    def test_rejects_an_angle_with_the_wrong_quantization(self) -> None:
        """Tests that a wrong angle format names the quantization."""
        wider = FixedPointArray.from_mantissas([0], 17, 16)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(1, wider)
        self.assertIn("(17, 16)", str(caught.exception))
        shorter = FixedPointArray.from_mantissas([0], 16, 15)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(1, shorter)
        self.assertIn("(16, 15)", str(caught.exception))


def main() -> None:
    """Plot cosine for amplitude scale 15 against the ideal value."""
    import matplotlib.pyplot as plt

    phases = np.arange(1 << PHASE_BITS, dtype=np.uint16)
    signed = phases.astype(np.int16).astype(np.int64)
    width, fraction = _ANGLE_QUANTIZATION
    angles = FixedPointArray.from_mantissas(signed, width, fraction)
    cosine = cordic_rotate(15, angles)
    turns = phases.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
    output = np.reshape(cosine.to_float(), -1)
    initial = int(_get_initial_vector(np.array([15]))[0])
    scale = 1 << _VECTOR_FRACTION
    ideal = (initial / scale) * CORDIC_GAIN * np.cos(turns)
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(turns, output, label="CORDIC cosine")
    axis.plot(turns, ideal, linestyle="--", label="Ideal")
    axis.set_xlabel("Phase (radians; input is a 16-bit fraction of a turn)")
    axis.set_ylabel("Cosine")
    axis.legend()
    figure.tight_layout()
    figure.savefig("cordic.png")


if __name__ == "__main__":
    main()

"""Rotation-mode CORDIC that returns a scaled cosine.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

from fp_array import FixedPointArray


ITERATIONS = 16
QUADRANT_SHIFT = 14
SCALE_MAX = 15
# Starting x for scale 15 is about full scale after the rotations.
FULL_SCALE_CONSTANT = 21223


def calculate_arctangent_table() -> np.ndarray:
    """Return ``atan(2**(-i)) / (2*pi)`` rounded half up, per step."""
    table = np.empty(ITERATIONS, dtype=np.int64)
    for index in range(ITERATIONS):
        turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
        table[index] = math.floor(turns * (1 << 16) + 0.5)
    return table


def calculate_cordic_gain() -> float:
    """Return the product of ``sqrt(1 + 2**(-2*i))`` over each step."""
    gain = 1.0
    for index in range(ITERATIONS):
        gain *= math.sqrt(1.0 + 2.0 ** (-2 * index))
    return gain


ARCTANGENT_TABLE = calculate_arctangent_table()
CORDIC_GAIN = calculate_cordic_gain()


def _check_magnitude_types(magnitudes: int | np.ndarray) -> None:
    """Raise TypeError unless magnitudes is an int or unsigned array."""
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


def _check_magnitude_range(magnitudes: int | np.ndarray) -> None:
    """Raise ValueError when a magnitude is outside 0 to 15."""
    if isinstance(magnitudes, np.ndarray):
        if magnitudes.size:
            found_min = int(np.min(magnitudes))
            found_max = int(np.max(magnitudes))
            if found_min < 0 or found_max > SCALE_MAX:
                raise ValueError(
                    "magnitudes must be between 0 and 15, "
                    f"got min {found_min} and max {found_max}"
                )
    elif magnitudes < 0 or magnitudes > SCALE_MAX:
        raise ValueError(
            f"magnitudes must be between 0 and 15, got {magnitudes}"
        )


def _check_angle_types(angles: FixedPointArray) -> None:
    """Raise TypeError unless angles is a FixedPointArray."""
    if not isinstance(angles, FixedPointArray):
        raise TypeError(
            "angles must be a FixedPointArray, "
            f"got {type(angles).__name__}"
        )


def _check_angle_quantization(angles: FixedPointArray) -> None:
    """Raise ValueError unless angles use quantization (16, 16)."""
    quantization = angles.get_quantization()
    if quantization != (16, 16):
        raise ValueError(
            "angles quantization must be (16, 16), "
            f"got {quantization}"
        )


def _check_shapes(
    magnitudes: int | np.ndarray, angles: FixedPointArray
) -> None:
    """Raise ValueError unless magnitudes broadcast onto the angles."""
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


def cordic_rotate(
    magnitudes: int | np.ndarray, angles: FixedPointArray
) -> FixedPointArray:
    """Return ``magnitudes / 15 * cos(angles)`` as a FixedPointArray.

    Parameters
    ----------
    magnitudes : int or numpy.ndarray
        Scaling factor from 0 to 15. An int, or an unsigned-integer
        array that broadcasts to ``angles`` without changing its shape.
    angles : FixedPointArray
        Angle in turns, quantization ``(16, 16)``.

    Returns
    -------
    FixedPointArray
        Cosine in signed Q1.15, quantization ``(16, 15)``.

    Raises
    ------
    TypeError
        If ``magnitudes`` or ``angles`` has the wrong type.
    ValueError
        If a scale, shape, or angle quantization is wrong.
    """
    _check_magnitude_types(magnitudes)
    _check_magnitude_range(magnitudes)
    _check_angle_types(angles)
    _check_angle_quantization(angles)
    _check_shapes(magnitudes, angles)
    angle_shape = angles.get_mantissas().shape
    scales = np.broadcast_to(
        np.asarray(magnitudes, dtype=np.int64), angle_shape
    )
    magnitude = _get_initial_vector(scales)
    remaining_angles, x_vector, y_vector = _pre_rotate(angles, magnitude)
    for index in range(ITERATIONS):
        directions = _calculate_directions(remaining_angles)
        shifted_x = x_vector >> index
        shifted_y = y_vector >> index
        x_vector = (x_vector - shifted_y * directions).re_quantize(
            16, 15
        )
        y_vector = (y_vector + shifted_x * directions).re_quantize(
            16, 15
        )
        # +1 when the remaining angle is >= 0, so the arctangent
        # is subtracted.
        arctangent = FixedPointArray.from_mantissas(
            int(ARCTANGENT_TABLE[index]), 16, 16
        )
        remaining_angles = (
            remaining_angles - arctangent * directions
        ).re_quantize(16, 16)
    return x_vector


def _get_initial_vector(scales: np.ndarray) -> np.ndarray:
    """Return the starting x integer for each scale."""
    total = np.zeros(scales.shape, dtype=np.int64)
    for bit in range(4):
        # Bit 0 is the least significant bit. Shift toward -infinity.
        shifted = FULL_SCALE_CONSTANT >> (4 - bit)
        total = total + ((scales >> bit) & 1) * shifted
    return total


def _pre_rotate(
    angles: FixedPointArray, magnitude: np.ndarray
) -> tuple[FixedPointArray, FixedPointArray, FixedPointArray]:
    """Return the remaining angle and put the magnitude on one axis.

    Quadrant 0 is +x, 1 is +y, 2 is -x, and 3 is -y.
    """
    phase = np.asarray(angles.get_mantissas(), dtype=np.int64)
    # Quadrant is the top two bits of the 16-bit pattern.
    pattern = phase & 0xFFFF
    quadrant = pattern >> QUADRANT_SHIFT
    offset = pattern & ((1 << QUADRANT_SHIFT) - 1)
    remaining_angles = FixedPointArray.from_mantissas(offset, 16, 16)
    zeros = np.zeros(magnitude.shape, dtype=np.int64)
    on_axis = [
        quadrant == 0,
        quadrant == 1,
        quadrant == 2,
        quadrant == 3,
    ]
    rotated_x = np.select(
        on_axis, [magnitude, zeros, -magnitude, zeros]
    )
    rotated_y = np.select(
        on_axis, [zeros, magnitude, zeros, -magnitude]
    )
    return (
        remaining_angles,
        FixedPointArray.from_mantissas(rotated_x, 16, 15),
        FixedPointArray.from_mantissas(rotated_y, 16, 15),
    )


def _calculate_directions(remaining_angles: FixedPointArray) -> np.ndarray:
    """Return +1 when the remaining angle is >= 0, otherwise -1."""
    return np.where(remaining_angles < 0, -1, 1)


class CORDICTests(unittest.TestCase):
    """Tests cosine across all four quadrants."""

    def _angles(self, phase: np.ndarray) -> FixedPointArray:
        """Return phase as signed (16, 16) with the same 16 bits."""
        unsigned = np.asarray(phase, dtype=np.uint16)
        signed = unsigned.astype(np.int16).astype(np.int64)
        return FixedPointArray.from_mantissas(signed, 16, 16)

    def _cosine_tolerance(self, magnitude: int) -> float:
        """Return the absolute cosine tolerance for this starting x."""
        # Half a step of angle error per iteration, plus one step per
        # shifted add, each grown by at most the rotation lengthening.
        angle_lsb = 2.0 * math.pi / (1 << 16)
        angle_error = 0.5 * ITERATIONS * angle_lsb
        shift_error = ITERATIONS * CORDIC_GAIN
        return abs(magnitude) * CORDIC_GAIN * angle_error + shift_error

    def test_arctangent_table_is_a_binary_angle(self) -> None:
        """Tests that table integers round ``atan(2**-i) / (2*pi)``."""
        one_turn = 1 << 16
        for index, entry in enumerate(ARCTANGENT_TABLE):
            turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            expected = math.floor(turns * one_turn + 0.5)
            self.assertEqual(int(entry), expected)
        self.assertEqual(int(ARCTANGENT_TABLE[0]), 1 << 13)
        self.assertEqual(int(ARCTANGENT_TABLE[14]), 1)
        self.assertEqual(int(ARCTANGENT_TABLE[15]), 0)

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
            [0, 1, (1 << QUADRANT_SHIFT) - 1, 16384 + 5, 32768 + 7, 65535]
        )
        angles = self._angles(phase)
        scales = np.full(phase.shape, 1, dtype=np.int64)
        magnitude = _get_initial_vector(scales)
        remaining, _x_vector, _y_vector = _pre_rotate(angles, magnitude)
        low_bits = (1 << QUADRANT_SHIFT) - 1
        np.testing.assert_array_equal(
            remaining.get_mantissas(),
            [0, 1, low_bits, 5, 7, low_bits],
        )
        self.assertEqual(remaining.get_quantization(), (16, 16))

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

    def test_output_quantization_is_q1_15(self) -> None:
        """Tests that the cosine uses quantization (16, 15)."""
        phases = np.array(
            [0, 1, 16384, 32768, 49152, 65535], dtype=np.uint16
        )
        cosine = cordic_rotate(15, self._angles(phases))
        self.assertEqual(cosine.get_quantization(), (16, 15))

    def test_all_scales_fit_in_signed_16_bits(self) -> None:
        """Tests that a 16-bit reset leaves x, y, and the angle unchanged."""
        phases = np.arange(1 << 16, dtype=np.uint16)
        scale_count = SCALE_MAX + 1
        phase_grid = np.broadcast_to(phases, (scale_count, phases.size))
        angles = self._angles(np.array(phase_grid, copy=True))
        scales = np.arange(scale_count, dtype=np.int64).reshape(
            scale_count, 1
        )
        magnitude = _get_initial_vector(
            np.broadcast_to(scales, angles.get_mantissas().shape)
        )
        remaining, x_vector, y_vector = _pre_rotate(angles, magnitude)

        def hold(
            vector: FixedPointArray, n: int, r: int
        ) -> FixedPointArray:
            before = vector.get_mantissas()
            low = -(1 << 15)
            high = (1 << 15) - 1
            self.assertGreaterEqual(int(np.min(before)), low)
            self.assertLessEqual(int(np.max(before)), high)
            held = vector.re_quantize(n, r)
            np.testing.assert_array_equal(held.get_mantissas(), before)
            self.assertEqual(held.get_quantization(), (n, r))
            return held

        x_vector = hold(x_vector, 16, 15)
        y_vector = hold(y_vector, 16, 15)
        remaining = hold(remaining, 16, 16)
        for index in range(ITERATIONS):
            directions = _calculate_directions(remaining)
            shifted_x = x_vector >> index
            shifted_y = y_vector >> index
            x_vector = hold(x_vector - shifted_y * directions, 16, 15)
            y_vector = hold(y_vector + shifted_x * directions, 16, 15)
            arctangent = FixedPointArray.from_mantissas(
                int(ARCTANGENT_TABLE[index]), 16, 16
            )
            remaining = hold(
                remaining - arctangent * directions, 16, 16
            )

    def test_scale_15_stays_inside_signed_16_bits(self) -> None:
        """Tests that amplitude scale 15 fits in a signed 16-bit word."""
        phases = np.arange(1 << 16, dtype=np.uint16)
        cosine = cordic_rotate(15, self._angles(phases))
        values = cosine.get_mantissas()
        self.assertGreaterEqual(int(np.min(values)), -(1 << 15))
        self.assertLessEqual(int(np.max(values)), (1 << 15) - 1)
        self.assertEqual(int(np.max(np.abs(values))), 32766)

    def test_cosine_at_every_phase(self) -> None:
        """Tests cosine at every phase for amplitude scale 15."""
        phases = np.arange(1 << 16, dtype=np.uint16)
        cosine = cordic_rotate(15, self._angles(phases))
        turns = phases.astype(float) * (2.0 * math.pi / (1 << 16))
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
        """Tests that an out-of-range scale names the offending value."""
        angles = self._angles(np.array([0, 1]))
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(16, angles)
        self.assertEqual(
            str(caught.exception),
            "magnitudes must be between 0 and 15, got 16",
        )
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(-1, angles)
        self.assertEqual(
            str(caught.exception),
            "magnitudes must be between 0 and 15, got -1",
        )
        scales = np.array([0, 20], dtype=np.uint8)
        with self.assertRaises(ValueError) as caught:
            cordic_rotate(scales, angles)
        self.assertEqual(
            str(caught.exception),
            "magnitudes must be between 0 and 15, got min 0 and max 20",
        )

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
    """Plot cosine for scale 15 against the ideal value."""
    import matplotlib.pyplot as plt

    phases = np.arange(1 << 16, dtype=np.uint16)
    signed = phases.astype(np.int16).astype(np.int64)
    angles = FixedPointArray.from_mantissas(signed, 16, 16)
    cosine = cordic_rotate(15, angles)
    turns = phases.astype(float) * (2.0 * math.pi / (1 << 16))
    output = np.reshape(cosine.to_float(), -1)
    initial = int(_get_initial_vector(np.array([15]))[0])
    ideal = (initial / (1 << 15)) * CORDIC_GAIN * np.cos(turns)
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.plot(turns, output, label="CORDIC cosine")
    axis.plot(turns, ideal, linestyle="--", label="Ideal")
    axis.set_xlabel("Phase (radians; input is a fraction of a turn)")
    axis.set_ylabel("Cosine")
    axis.legend()
    figure.tight_layout()
    figure.savefig("cordic.png")


if __name__ == "__main__":
    main()

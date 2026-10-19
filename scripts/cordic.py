"""Fixed-point rotation-mode CORDIC sine and cosine.

Phase is an unsigned 16-bit binary angle (U0.16): ``2**16`` codes is
one full turn, so full scale is ``2*pi`` radians. The top two bits
select the quadrant and the low 14 bits are the residual inside that
quadrant. The residual and the arctangent table stay in that unit.
Code ``m`` is ``m / 2**16`` of a turn. There is no conversion to
radians.

The quadrant step is a 90-degree pre-rotation, which is a swap and
negate in hardware:

* quadrant 0: ``(x, y)``
* quadrant 1: ``(-y, x)``
* quadrant 2: ``(-x, -y)``
* quadrant 3: ``(y, -x)``

The residual is then in ``[0, 1/4)`` turn and is applied with shift-add
iterations. Iteration ``i`` grows the vector length by
``sqrt(1 + 2**(-2*i))``. The product of those factors is the gain
``K``. The datapath multiplies by a quantized ``1/K`` and saturates
back to the vector format. For an input of ``(1, 0)``, the returned
pair is cosine and sine.
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
# Signed width of the angle word. The residual is at most 2**14 - 1
# codes and the first table entry is 2**13 codes, so a 16-bit signed
# word holds both and still has room when an iteration steps past zero.
ANGLE_WIDTH = 16


def cordic_gain(n_rotations: int) -> float:
    """Return the CORDIC magnitude growth ``K``.

    Iteration ``i`` multiplies the vector length by
    ``sqrt(1 + 2**(-2*i))``. ``K`` is the product of those factors from
    ``i = 0`` through ``n_rotations - 1``. Hardware should not recompute
    this product: quantize ``1/K`` once into the vector format and use
    that constant.

    Parameters
    ----------
    n_rotations : int
        Number of shift-add iterations. Zero returns 1.

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
        gain *= math.sqrt(1.0 + 2.0 ** (-2 * index))
    return gain


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
    """Rotation-mode CORDIC with a 90-degree quadrant pre-rotation.

    ``x`` and ``y`` use signed format ``(n_x, r_x)``. The residual angle
    is a signed fraction of a turn with ``PHASE_BITS`` fractional bits,
    the same LSB as the U0.16 phase code. Phase inputs are unsigned
    16-bit codes. Iterations keep full precision; only the
    gain-compensated output is narrowed to ``(n_x, r_x)``.
    """

    def __init__(
        self,
        n_rotations: int = 16,
        n_x: int = 16,
        r_x: int = 13,
    ) -> None:
        """Build the arctangent table and the quantized reciprocal gain.

        Table entry ``i`` is ``atan(2**(-i)) / (2*pi)``, floored into
        the phase-code LSB. ``atan(1) / (2*pi)`` is exactly 1/8 of a
        turn, so the first code is ``2**13``.

        Parameters
        ----------
        n_rotations : int, optional
            Shift-add iterations. Default is 16.
        n_x : int, optional
            Signed width of ``x`` and ``y``. Default is 16.
        r_x : int, optional
            Fractional bits of ``x`` and ``y``. Default is 13.

        Raises
        ------
        ValueError
            If the iteration count or a format is not valid.
        """
        self._gain: float = cordic_gain(n_rotations)
        self._n_rotations: int = int(n_rotations)
        self._n_x: int = int(n_x)
        self._r_x: int = int(r_x)
        turns = [
            math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            for index in range(self._n_rotations)
        ]
        self._angle_lut: FixedPointArray = FixedPointArray(
            turns, ANGLE_WIDTH, PHASE_BITS
        )
        self._inv_gain: FixedPointArray = FixedPointArray(
            1.0 / self._gain, self._n_x, self._r_x
        )

    @property
    def n_rotations(self) -> int:
        """Return the number of shift-add iterations.

        Returns
        -------
        int
            Iteration count used for the gain and the angle table.
        """
        return self._n_rotations

    @property
    def gain(self) -> float:
        """Return the CORDIC growth ``K`` for this iteration count.

        Returns
        -------
        float
            Product of ``sqrt(1 + 2**(-2*i))`` over the iterations.
        """
        return self._gain

    @property
    def inverse_gain(self) -> FixedPointArray:
        """Return the quantized ``1/K`` constant in the vector format.

        Returns
        -------
        FixedPointArray
            Reciprocal of :attr:`gain`, floored into ``(n_x, r_x)``.
            Rotation multiplies by this constant. The returned array is
            a copy.
        """
        return FixedPointArray.from_mantissas(
            self._inv_gain.values, self._inv_gain.n, self._inv_gain.r
        )

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
        """Pre-rotate ``(x, y)`` by ``quadrant`` right angles.

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
        """Return a 14-bit quadrant offset in U0.16 turn units.

        Parameters
        ----------
        offset : numpy.ndarray
            Low 14 phase bits. Code ``m`` is already ``m / 2**16`` of a
            turn, so the bits are stored as the angle mantissa.

        Returns
        -------
        FixedPointArray
            Residual in ``[0, 1/4)`` turn, as signed
            ``(ANGLE_WIDTH, PHASE_BITS)`` codes.
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
        """Apply one shift-add rotation toward the residual angle.

        Parameters
        ----------
        x_vector : FixedPointArray
            Current x component.
        y_vector : FixedPointArray
            Current y component.
        angle : FixedPointArray
            Remaining angle. A negative value reverses the rotation.
        index : int
            Iteration index. The shifted term is an arithmetic right
            shift of ``index`` bits, then an add or subtract.

        Returns
        -------
        tuple of FixedPointArray
            Updated ``(x, y, angle)``. Both vector updates use the
            pre-update components. The angle moves toward zero by
            table entry ``index``, which is ``atan(2**(-index))`` in
            fractions of a turn.
        """
        direction = np.where(angle < 0, -1, 1)
        shifted_x = x_vector >> index
        shifted_y = y_vector >> index
        next_x = x_vector - shifted_y * direction
        next_y = y_vector + shifted_x * direction
        step = self._angle_lut[index]
        next_angle = angle - step * direction
        return next_x, next_y, next_angle

    def _compensate(
        self,
        x_vector: FixedPointArray,
        y_vector: FixedPointArray,
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Remove the CORDIC gain and narrow to the vector format.

        Parameters
        ----------
        x_vector : FixedPointArray
            X component still scaled by ``K``.
        y_vector : FixedPointArray
            Y component still scaled by ``K``.

        Returns
        -------
        tuple of FixedPointArray
            Gain-compensated vector, saturated into ``(n_x, r_x)``.
        """
        x_out = (x_vector * self._inv_gain).re_quantize(self._n_x, self._r_x)
        y_out = (y_vector * self._inv_gain).re_quantize(self._n_x, self._r_x)
        return x_out, y_out

    def rotate(
        self, x: Any, y: Any, phase: Any
    ) -> tuple[FixedPointArray, FixedPointArray]:
        """Rotate ``(x, y)`` by an unsigned 16-bit phase.

        Parameters
        ----------
        x : array-like of float
            Initial x components.
        y : array-like of float
            Initial y components.
        phase : array-like of int
            Unsigned phase codes in ``[0, 65535]``. ``2**16`` codes is
            one full turn. The low 14 bits are the residual angle, in
            the same unit as the arctangent table.

        Returns
        -------
        tuple of FixedPointArray
            Rotated ``(x, y)`` in the vector format. For input
            ``(1, 0)`` these are cosine and sine of ``phase``.

        Raises
        ------
        TypeError
            If ``phase`` is not an integer array.
        ValueError
            If a phase code is outside ``[0, 65535]``, or if ``x``,
            ``y``, and ``phase`` do not broadcast.
        """
        phase_codes = self._phase_codes(phase)
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
        quadrant = np.asarray(phase_codes >> OFFSET_BITS, dtype=np.int64)
        offset = np.asarray(phase_codes & ((1 << OFFSET_BITS) - 1))
        x_vector, y_vector = self._prerotate(x_vector, y_vector, quadrant)
        angle = self._residual_angle(offset)
        for index in range(self._n_rotations):
            x_vector, y_vector, angle = self._microrotation(
                x_vector, y_vector, angle, index
            )
        return self._compensate(x_vector, y_vector)


def sweep_and_plot(
    cordic: CORDIC | None = None,
    output_path: str = "cordic.png",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, plt.Figure]:
    """Sweep every phase code and plot cosine with its absolute error.

    Parameters
    ----------
    cordic : CORDIC, optional
        Model to sweep. The default is a :class:`CORDIC` with the
        default formats.
    output_path : str, optional
        Path of the saved figure. Default is ``cordic.png``.

    Returns
    -------
    tuple
        Phase in radians, CORDIC cosine, absolute error against
        ``numpy.cos``, and the Matplotlib figure.
    """
    model = CORDIC() if cordic is None else cordic
    phase_codes = np.arange(1 << PHASE_BITS, dtype=np.uint16)
    angles = phase_codes.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
    cosine, _sine = model.rotate(1, 0, phase_codes)
    output = np.reshape(cosine.to_float(), -1)
    ideal = np.cos(angles)
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


def _absolute_tolerance(cordic: CORDIC) -> float:
    """Return an absolute sine/cosine tolerance for ``cordic``.

    The angle LSB is one phase code, ``2*pi/2**PHASE_BITS`` radians.
    Flooring each arctangent constant can miss the residual by one such
    LSB per iteration, and ``|d(sin)/d(theta)|`` and ``|d(cos)/d(theta)|``
    are at most 1. Each microrotation also truncates a shifted component
    by up to one vector LSB. The floored ``1/K`` shortens a magnitude-K
    vector by up to ``K`` vector LSBs, and the output quantizer adds one
    more.

    Parameters
    ----------
    cordic : CORDIC
        Model whose iteration count and vector format set the tolerance.

    Returns
    -------
    float
        Absolute tolerance.
    """
    _vector_bits, fraction_bits = cordic.vector_format
    angle_lsb = 2.0 * math.pi / (1 << PHASE_BITS)
    vector_lsb = 2.0 ** (-fraction_bits)
    angle_error = cordic.n_rotations * angle_lsb
    shift_error = cordic.n_rotations * vector_lsb
    gain_error = (cordic.gain + 1.0) * vector_lsb
    return angle_error + shift_error + gain_error


class CORDICTests(unittest.TestCase):
    """Tests sine and cosine across all four quadrants."""

    def test_arctangent_table_is_a_binary_angle(self) -> None:
        """Tests that table codes are ``atan(2**-i)`` in U0.16 turns."""
        cordic = CORDIC()
        scale = 1 << PHASE_BITS
        for index, code in enumerate(cordic._angle_lut.values):
            turns = math.atan(2.0 ** (-index)) / (2.0 * math.pi)
            expected = math.floor(turns * scale)
            self.assertEqual(int(code), expected)
        self.assertEqual(int(cordic._angle_lut.values[0]), 1 << 13)

    def test_residual_keeps_the_phase_code(self) -> None:
        """Tests that a quadrant offset is stored without scaling."""
        cordic = CORDIC()
        offset = np.array([0, 1, (1 << OFFSET_BITS) - 1])
        residual = cordic._residual_angle(offset)
        np.testing.assert_array_equal(residual.values, offset)
        self.assertEqual(residual.r, PHASE_BITS)

    def test_gain_is_the_iteration_product(self) -> None:
        """Tests that ``K`` is the product of the per-iteration gains."""
        cordic = CORDIC()
        self.assertEqual(cordic.gain, cordic_gain(16))
        scale = cordic.inverse_gain
        product = float(scale.to_float()[0]) * cordic.gain
        # floor(1/K) is at most one vector LSB below 1/K.
        shortfall = cordic.gain * (2.0 ** (-scale.r))
        self.assertAlmostEqual(product, 1.0, delta=shortfall)
        self.assertLessEqual(product, 1.0)

    def test_axes_match_quadrant_pre_rotation(self) -> None:
        """Tests the four axes, where the residual angle is zero."""
        cordic = CORDIC()
        phases = np.array([0, 16384, 32768, 49152], dtype=np.uint16)
        cosine, sine = cordic.rotate(1, 0, phases)
        tolerance = _absolute_tolerance(cordic)
        expected_cos = np.array([1.0, 0.0, -1.0, 0.0])
        expected_sin = np.array([0.0, 1.0, 0.0, -1.0])
        np.testing.assert_allclose(
            cosine.to_float(), expected_cos, atol=tolerance
        )
        np.testing.assert_allclose(
            sine.to_float(), expected_sin, atol=tolerance
        )

    def test_sin_cos_all_quadrants(self) -> None:
        """Tests sine and cosine at every phase code in all quadrants."""
        cordic = CORDIC()
        phases = np.arange(0, 1 << PHASE_BITS, dtype=np.uint16)
        cosine, sine = cordic.rotate(1, 0, phases)
        angles = phases.astype(float) * (2.0 * math.pi / (1 << PHASE_BITS))
        tolerance = _absolute_tolerance(cordic)
        np.testing.assert_allclose(
            np.reshape(cosine.to_float(), -1), np.cos(angles), atol=tolerance
        )
        np.testing.assert_allclose(
            np.reshape(sine.to_float(), -1), np.sin(angles), atol=tolerance
        )

    def test_phase_codes_are_rejected_when_out_of_range(self) -> None:
        """Tests rejection of non-integer and out-of-range phase codes."""
        cordic = CORDIC()
        with self.assertRaises(TypeError):
            cordic.rotate(1, 0, 0.5)
        with self.assertRaises(ValueError):
            cordic.rotate(1, 0, -1)
        with self.assertRaises(ValueError):
            cordic.rotate(1, 0, 65536)


def main() -> None:
    """Run the CORDIC tests, then save a full-phase cosine plot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="cordic.png")
    args = parser.parse_args()
    unittest.main(argv=["cordic"], exit=False)
    sweep_and_plot(output_path=args.output)


if __name__ == "__main__":
    main()

"""Fixed-point CORDIC rotation and exhaustive cosine validation."""

import argparse
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

try:
    from .fp_array import FixedPointArray
except ImportError:
    from fp_array import FixedPointArray


class CORDIC:
    """Compute cosine with a fixed-point rotation-mode CORDIC."""

    def __init__(self, n_rotations=16, n_x=16, r_x=13, n_z=16, r_z=11):
        """Initialize CORDIC iteration count and vector/angle formats."""
        self._n_rotations = n_rotations
        self._n_x = n_x
        self._r_x = r_x
        self._n_z = n_z
        self._r_z = r_z
        self._angle_lut = FixedPointArray(
            np.arctan(2.0 ** -np.arange(n_rotations)), n_z, r_z
        )
        self._gain = FixedPointArray(1 / 1.64676, n_x, r_x)

    def _rotation_inputs(self, x, y, phase):
        """Quantize vector inputs and broadcast unsigned U0.16 phase codes."""
        x_fp = FixedPointArray(x, self._n_x, self._r_x)
        y_fp = FixedPointArray(y, self._n_x, self._r_x)
        phase_codes = np.asarray(phase)
        if not np.issubdtype(phase_codes.dtype, np.integer):
            raise TypeError("phase must contain unsigned U0.16 integer codes")
        if np.any(phase_codes < 0) or np.any(phase_codes > 0xFFFF):
            raise ValueError("U0.16 phase codes must be in [0, 65535]")
        try:
            x_values, y_values, phase_codes = np.broadcast_arrays(
                x_fp.values, y_fp.values, phase_codes
            )
        except ValueError as error:
            raise ValueError("x, y, and phase must be broadcastable") from error
        return (
            FixedPointArray._from_mantissas(x_values, x_fp.n, x_fp.r),
            FixedPointArray._from_mantissas(y_values, y_fp.n, y_fp.r),
            phase_codes.astype(np.uint16),
        )

    def _phase_to_rotation_angle(self, x, y, phase_codes):
        """Decode quadrant/offset bits into a signed CORDIC angle and vector."""
        quadrant = (phase_codes >> 14).astype(np.uint8)
        offset = phase_codes & 0x3FFF
        offset_radians = offset.astype(float) * (np.pi / (2 * 16384))

        # Rotate by the signed residual and negate only x in quadrants 2 and 3.
        angle = np.where((quadrant == 0) | (quadrant == 2),
                         offset_radians, -offset_radians)
        flip_x = (quadrant == 1) | (quadrant == 2)
        x[flip_x] = -x[flip_x]
        z = FixedPointArray(angle, self._n_z, self._r_z)
        return x, y, z

    def iteration(self, x, y, phase):
        """Rotate inputs for U0.16 phase codes and return mantissa histories."""
        x, y, phase_codes = self._rotation_inputs(x, y, phase)
        x, y, z = self._phase_to_rotation_angle(x, y, phase_codes)
        count = z.values.size
        history_size = self._n_rotations + 3
        x_history = np.zeros((history_size, count), dtype=object)
        y_history = np.zeros_like(x_history)
        z_history = np.zeros_like(x_history)
        directions = np.zeros((self._n_rotations, count), dtype=np.int8)

        x_history[0] = x.values.reshape(-1)
        y_history[0] = y.values.reshape(-1)
        z_history[0] = z.values.reshape(-1)
        x_history[1] = x.values.reshape(-1)
        y_history[1] = y.values.reshape(-1)
        z_history[1] = z.values.reshape(-1)

        for index in range(self._n_rotations):
            direction = np.where(z_history[index + 1] < 0, -1, 1)
            directions[index] = direction
            x_current = FixedPointArray._from_mantissas(
                x_history[index + 1], self._n_x, self._r_x
            )
            y_current = FixedPointArray._from_mantissas(
                y_history[index + 1], self._n_x, self._r_x
            )
            z_current = FixedPointArray._from_mantissas(
                z_history[index + 1], self._n_z, self._r_z
            )
            x_next = x_current - (y_current * direction >> index)
            y_next = y_current + (x_current * direction >> index)
            z_next = z_current - self._angle_lut[index] * direction
            x_history[index + 2] = x_next.values
            y_history[index + 2] = y_next.values
            z_history[index + 2] = z_next.values

        x_final = FixedPointArray._from_mantissas(
            x_history[-2], self._n_x, self._r_x
        ) * self._gain
        y_final = FixedPointArray._from_mantissas(
            y_history[-2], self._n_x, self._r_x
        ) * self._gain
        x_final.re_quantize(self._n_x, self._r_x)
        y_final.re_quantize(self._n_x, self._r_x)
        x_history[-1] = x_final.values
        y_history[-1] = y_final.values
        z_history[-1] = z_history[-2]
        return x_history, y_history, z_history, directions


def sweep_and_plot(cordic=None, output_path="cordic.png"):
    """Sweep all U0.16 phases and plot output with absolute quantization error."""
    cordic = cordic or CORDIC()
    phase_codes = np.arange(1 << 16, dtype=np.uint16)
    angles = phase_codes.astype(float) * (2 * np.pi / (1 << 16))

    x_history, _, _, _ = cordic.iteration(1, 0, phase_codes)
    output = np.asarray(x_history[-1], dtype=float) / (1 << cordic._r_x)
    ideal_cosine = np.cos(angles)
    absolute_error = np.abs(ideal_cosine - output)

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
        ideal_cosine,
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


class CORDICTests(unittest.TestCase):
    """Test quadrant mapping and end-to-end CORDIC cosine output."""

    def test_quadrant_mapping_and_cosine(self):
        """Check representative offsets in all U0.16 quadrants."""
        cordic = CORDIC()
        offset_code = 4096
        phase_codes = np.array(
            [offset_code, 16384 + offset_code,
             32768 + offset_code, 49152 + offset_code],
            dtype=np.uint16,
        )
        x, y, phases = cordic._rotation_inputs(1, 0, phase_codes)
        x, y, z = cordic._phase_to_rotation_angle(x, y, phases)
        expected_angles = np.array(
            [1, 1, -1, -1], dtype=float
        ) * offset_code * (2 * np.pi / 65536)
        np.testing.assert_allclose(
            z.to_float(), expected_angles, atol=2 ** -cordic._r_z
        )
        expected_x_flip = np.array([False, True, True, False])
        np.testing.assert_array_equal(x.values < 0, expected_x_flip)
        np.testing.assert_array_equal(y.values, np.zeros(4, dtype=object))

        x_history, _, _, _ = cordic.iteration(1, 0, phase_codes)
        actual = np.asarray(x_history[-1], dtype=float) / (1 << cordic._r_x)
        ideal = np.cos(phase_codes.astype(float) * (2 * np.pi / 65536))
        np.testing.assert_allclose(actual, ideal, atol=0.01)
        diagnostics = np.column_stack((
            phase_codes,
            z.to_float(),
            x.to_float(),
            y.to_float(),
            actual,
            ideal,
        ))
        np.savetxt(
            Path(__file__).with_name("cordic_quadrant_test.txt"),
            diagnostics,
            fmt=["%u", "%.9f", "%.9f", "%.9f", "%.9f", "%.9f"],
            header="phase_code mapped_angle x_after_map y_after_map cordic_cos ideal_cos",
        )


def main():
    """Run CORDIC tests, then sweep and save the resulting plot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="cordic.png")
    args = parser.parse_args()
    unittest.main(argv=["cordic"], exit=False)
    sweep_and_plot(output_path=args.output)


if __name__ == "__main__":
    main()

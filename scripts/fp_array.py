"""Fixed-point arrays with explicit quantization tracking."""

import numbers
import unittest

import numpy as np


class FixedPointArray:
    """An array of signed fixed-point mantissas.

    ``n`` is the signed mantissa width and ``r`` is its fractional-bit count.
    Arithmetic results retain all available precision and grow ``n`` as
    necessary; use :meth:`re_quantize` to explicitly narrow a result.
    """

    def __init__(self, values, n=16, r=8):
        self._validate_format(n, r)
        self._n = int(n)
        self._r = int(r)
        self.set_values(values)

    @staticmethod
    def _validate_format(n, r):
        if not isinstance(n, numbers.Integral) or n < 1:
            raise ValueError("n must be a positive integer")
        if not isinstance(r, numbers.Integral) or r < 0:
            raise ValueError("r must be a non-negative integer")

    @staticmethod
    def _width_for_values(values):
        """Return the minimum signed width that contains all integer values."""
        values = np.asarray(values, dtype=object)
        if values.size == 0:
            return 1
        minimum = min(int(value) for value in values.flat)
        maximum = max(int(value) for value in values.flat)
        width = 1
        while minimum < -(1 << (width - 1)) or maximum > (1 << (width - 1)) - 1:
            width += 1
        return width

    @staticmethod
    def _saturate(mantissas, n):
        lower = -(1 << (n - 1))
        upper = (1 << (n - 1)) - 1
        return np.asarray(np.clip(mantissas, lower, upper), dtype=object)

    @classmethod
    def _from_mantissas(cls, mantissas, n, r):
        result = cls.__new__(cls)
        result._n = int(n)
        result._r = int(r)
        result._x = np.asarray(mantissas, dtype=object)
        if result._x.ndim == 0:
            result._x = result._x.reshape(1)
        return result

    @staticmethod
    def _integer_array(value):
        array = np.asarray(value)
        if not np.issubdtype(array.dtype, np.integer):
            raise TypeError("operand must be an integer or an array of integers")
        return array.astype(object)

    @property
    def values(self):
        """A copy of the stored integer mantissas."""
        return np.asarray(self._x, dtype=object).copy()

    @property
    def n(self):
        """Signed mantissa width."""
        return self._n

    @property
    def r(self):
        """Number of fractional bits."""
        return self._r

    @property
    def quantization(self):
        """The ``(n, r)`` quantization tuple."""
        return self._n, self._r

    def set_values(self, values):
        """Quantize real values into the current signed fixed-point format."""
        values = np.asarray(values)
        quantized = np.floor(values * (1 << self._r))
        self._x = self._saturate(quantized, self._n).astype(int)
        if self._x.ndim == 0:
            self._x = self._x.reshape(1)

    def to_float(self):
        """Return the represented values as floating-point numbers."""
        return np.asarray(self._x, dtype=float) / (1 << self._r)

    def re_quantize(self, n, r):
        """Change format in place, truncating dropped LSBs and saturating."""
        self._validate_format(n, r)
        n, r = int(n), int(r)
        if r < self._r:
            shift = self._r - r
            divisor = 1 << shift
            mantissas = np.where(
                self._x < 0,
                -np.floor_divide(-self._x, divisor),
                np.floor_divide(self._x, divisor),
            )
        elif r > self._r:
            mantissas = self._x * (1 << (r - self._r))
        else:
            mantissas = self._x.copy()
        self._x = self._saturate(mantissas, n)
        self._n, self._r = n, r
        return self

    def _as_fixed_integer_operand(self, other):
        integers = self._integer_array(other)
        return integers * (1 << self._r)

    def __add__(self, other):
        if isinstance(other, FixedPointArray):
            r = max(self._r, other._r)
            left = self._x * (1 << (r - self._r))
            right = other._x * (1 << (r - other._r))
            mantissas = left + right
            n = max(self._n + (r - self._r), other._n + (r - other._r)) + 1
        elif isinstance(other, (numbers.Integral, np.ndarray, list, tuple)):
            mantissas = self._x + self._as_fixed_integer_operand(other)
            n = max(self._n, self._width_for_values(mantissas))
            r = self._r
        else:
            return NotImplemented
        n = max(n, self._width_for_values(mantissas))
        return self._from_mantissas(mantissas, n, r)

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, FixedPointArray):
            mantissas = self._x * other._x
            r = self._r + other._r
            n = max(self._n + other._n, self._width_for_values(mantissas))
        elif isinstance(other, (numbers.Integral, np.ndarray, list, tuple)):
            integers = self._integer_array(other)
            mantissas = self._x * integers
            r = self._r
            integer_width = self._width_for_values(integers)
            n = max(self._n + integer_width, self._width_for_values(mantissas))
        else:
            return NotImplemented
        return self._from_mantissas(mantissas, n, r)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __neg__(self):
        mantissas = -self._x
        n = max(self._n, self._width_for_values(mantissas))
        return self._from_mantissas(mantissas, n, self._r)

    def __sub__(self, other):
        if isinstance(other, FixedPointArray):
            return self + (-other)
        if isinstance(other, (numbers.Integral, np.ndarray, list, tuple)):
            return self + (-self._integer_array(other))
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, (numbers.Integral, np.ndarray, list, tuple)):
            return (-self) + other
        return NotImplemented

    def __lshift__(self, shift):
        shifts = self._integer_array(shift)
        if np.any(shifts < 0):
            raise ValueError("shift counts must be non-negative")
        try:
            mantissas = np.left_shift(self._x, shifts)
        except ValueError as error:
            raise ValueError("shift counts must be broadcastable to the array") from error
        n = max(self._n + (int(np.max(shifts)) if shifts.size else 0),
                self._width_for_values(mantissas))
        return self._from_mantissas(mantissas, n, self._r)

    def __rshift__(self, shift):
        shifts = self._integer_array(shift)
        if np.any(shifts < 0):
            raise ValueError("shift counts must be non-negative")
        try:
            mantissas = np.right_shift(self._x, shifts)
        except ValueError as error:
            raise ValueError("shift counts must be broadcastable to the array") from error
        return self._from_mantissas(mantissas, self._n, self._r)

    def _comparison_operand(self, other):
        if isinstance(other, FixedPointArray):
            r = max(self._r, other._r)
            left = self._x * (1 << (r - self._r))
            right = other._x * (1 << (r - other._r))
            return left, right
        if isinstance(other, (numbers.Integral, np.ndarray, list, tuple)):
            return self._x, self._as_fixed_integer_operand(other)
        return NotImplemented, NotImplemented

    def __lt__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return NotImplemented
        return np.less(left, right)

    def __le__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return NotImplemented
        return np.less_equal(left, right)

    def __gt__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return NotImplemented
        return np.greater(left, right)

    def __ge__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return NotImplemented
        return np.greater_equal(left, right)

    def __eq__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return False
        return np.equal(left, right)

    def __ne__(self, other):
        left, right = self._comparison_operand(other)
        if left is NotImplemented:
            return True
        return np.not_equal(left, right)

    def __getitem__(self, key):
        return self._from_mantissas(np.asarray(self._x[key]), self._n, self._r)

    def __setitem__(self, key, value):
        if isinstance(value, FixedPointArray):
            if value._r != self._r:
                raise ValueError("assigned FixedPointArray must have matching r")
            mantissas = value._x
        else:
            mantissas = self._as_fixed_integer_operand(value)
        updated = self._x.copy()
        updated[key] = mantissas
        self._x = self._saturate(updated, self._n)

    def __iter__(self):
        for value in self._x:
            yield self._from_mantissas(np.asarray(value), self._n, self._r)

    def __array__(self, dtype=None, copy=None):
        result = np.asarray(self._x, dtype=dtype)
        return result.copy() if copy else result

    def __repr__(self):
        return f"FixedPointArray({self.to_float()}, n={self._n}, r={self._r})"


class FixedPointArrayTests(unittest.TestCase):
    def test_constructor_and_saturation(self):
        value = FixedPointArray([-100, -1.25, 0.5, 100], n=8, r=4)
        np.testing.assert_array_equal(value.values, [-128, -20, 8, 127])
        self.assertEqual(value.quantization, (8, 4))

    def test_addition_preserves_fractional_precision_and_grows_width(self):
        left = FixedPointArray([1.25], n=8, r=2)
        right = FixedPointArray([0.125], n=8, r=3)
        result = left + right
        np.testing.assert_allclose(result.to_float(), [1.375])
        self.assertEqual(result.r, 3)
        self.assertGreaterEqual(result.n, 10)
        np.testing.assert_array_equal((left + 2).values, [13])

    def test_multiplication_preserves_all_product_bits(self):
        left = FixedPointArray([1.25], n=8, r=2)
        right = FixedPointArray([-0.75], n=8, r=3)
        result = left * right
        np.testing.assert_allclose(result.to_float(), [-0.9375])
        self.assertEqual(result.quantization, (16, 5))
        np.testing.assert_array_equal((left * np.array([2])).values, [10])
        self.assertEqual((left * 2).r, left.r)

    def test_reverse_arithmetic_and_subtraction(self):
        value = FixedPointArray([1.5, -0.5], n=8, r=2)
        np.testing.assert_allclose((2 + value).to_float(), [3.5, 1.5])
        np.testing.assert_allclose((3 - value).to_float(), [1.5, 3.5])
        np.testing.assert_allclose((-value).to_float(), [-1.5, 0.5])

    def test_requantize_truncates_and_saturates(self):
        value = FixedPointArray([1.375, -1.375], n=16, r=3)
        value.re_quantize(4, 1)
        np.testing.assert_array_equal(value.values, [2, -2])
        self.assertEqual(value.quantization, (4, 1))

    def test_shifts_operate_on_mantissas(self):
        value = FixedPointArray([1.5, -1.5], n=8, r=2)
        left = value << 3
        right = value >> 1
        np.testing.assert_array_equal(left.values, [48, -48])
        self.assertEqual(left.r, value.r)
        self.assertGreaterEqual(left.n, value.n + 3)
        np.testing.assert_array_equal(right.values, [3, -3])
        self.assertEqual(right.quantization, value.quantization)
        np.testing.assert_array_equal(value << np.array([1, 2]), [12, -24])

    def test_comparisons_align_quantization_and_return_masks(self):
        left = FixedPointArray([0.5, 1.5, -1], n=8, r=2)
        right = FixedPointArray([0.25, 1.75, -1], n=8, r=3)
        np.testing.assert_array_equal(left < right, [False, True, False])
        np.testing.assert_array_equal(left > right, [True, False, False])
        np.testing.assert_array_equal(left == right, [False, False, True])
        np.testing.assert_array_equal(left >= 1, [False, True, False])

    def test_indexing_and_mask_assignment(self):
        value = FixedPointArray([0.5, 1, 1.5], n=8, r=2)
        self.assertEqual(value[1].quantization, value.quantization)
        value[value > 1] = FixedPointArray([2], n=8, r=2)
        np.testing.assert_allclose(value.to_float(), [0.5, 1, 2])

    def test_rejects_non_integer_shifts_and_operands(self):
        value = FixedPointArray([1], n=8, r=2)
        with self.assertRaises(TypeError):
            _ = value * 1.5
        with self.assertRaises(ValueError):
            _ = value << -1


def main():
    unittest.main()


if __name__ == "__main__":
    main()

"""Signed fixed-point arrays.

Each value has format ``(n, r)``: ``n`` is the two's-complement width
and ``r`` is the number of fractional bits.
"""

from __future__ import annotations

import numbers
import unittest
from typing import Any

import numpy as np


def _calculate_bit_width(value: int) -> int:
    """Return the two's-complement width of one integer.

    Parameters
    ----------
    value : int
        Integer to measure.

    Returns
    -------
    int
        Smallest ``n`` such that ``value`` fits in a signed ``n``-bit word.
    """
    if value >= 0:
        return value.bit_length() + 1
    return (~value).bit_length() + 1


def _calculate_signed_width(values: np.ndarray) -> int:
    """Return the signed width that holds every mantissa.

    Parameters
    ----------
    values : numpy.ndarray
        Integer mantissas. May be empty.

    Returns
    -------
    int
        Minimum signed width. An empty array returns 1.
    """
    if values.size == 0:
        return 1
    low = int(np.min(values))
    high = int(np.max(values))
    return max(_calculate_bit_width(low), _calculate_bit_width(high))


def _convert_to_integer_array(values: Any) -> np.ndarray:
    """Return ``values`` as an object array of Python integers.

    Parameters
    ----------
    values : int or array-like of int
        Scalar integer or an array, list, or tuple of integers.

    Returns
    -------
    numpy.ndarray
        Object array of Python integers. A scalar is zero-dimensional so
        it can broadcast.

    Raises
    ------
    TypeError
        If ``values`` is not an integer or an array of integers.
    """
    message = "operand must be an integer or an array of integers"
    if isinstance(values, bool):
        raise TypeError(message)
    if isinstance(values, numbers.Integral):
        return np.array(int(values), dtype=object)
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.integer):
        return array.astype(object)
    if array.dtype != object:
        raise TypeError(message)
    flat = np.reshape(array, -1)
    result = np.empty(flat.shape, dtype=object)
    for index, value in enumerate(flat):
        if isinstance(value, bool) or not isinstance(value, numbers.Integral):
            raise TypeError(message)
        result[index] = int(value)
    return np.reshape(result, array.shape)


def _calculate_scaled_integers(
    values: Any, fractional_bits: int
) -> np.ndarray:
    """Scale integer operands into ``fractional_bits``.

    Parameters
    ----------
    values : int or array-like of int
        Real integer values, not already-quantized mantissas.
    fractional_bits : int
        Fractional width of the fixed-point operand they combine with.

    Returns
    -------
    numpy.ndarray
        ``values * 2**fractional_bits`` as Python integers.
    """
    return _convert_to_integer_array(values) * (1 << fractional_bits)


def _is_integral_operand(value: Any) -> bool:
    """Return whether ``value`` is handled on the integer-operand path.

    Parameters
    ----------
    value : object
        Candidate operand.

    Returns
    -------
    bool
        True for an integer, list, tuple, or NumPy array. Arrays are
        checked for an integer dtype by the caller.
    """
    return isinstance(value, (numbers.Integral, np.ndarray, list, tuple))


def _convert_to_object_integers(values: np.ndarray) -> np.ndarray:
    """Convert integral numbers to an object array of Python integers.

    Parameters
    ----------
    values : numpy.ndarray
        Floored real values or integers.

    Returns
    -------
    numpy.ndarray
        Object array of ``int`` with the same shape as ``values``.
    """
    flat = np.reshape(values, -1)
    result = np.empty(flat.shape, dtype=object)
    for index, value in enumerate(flat):
        result[index] = int(value)
    return np.reshape(result, values.shape)


def _quantize(values: Any, n: int, r: int) -> np.ndarray:
    """Floor real ``values`` into saturated ``(n, r)`` mantissas.

    Parameters
    ----------
    values : array-like of float
        Real numbers to quantize.
    n : int
        Signed width, including the sign bit.
    r : int
        Fractional bit count.

    Returns
    -------
    numpy.ndarray
        Object array of Python-integer mantissas. A scalar input has
        shape ``(1,)``.
    """
    scaled = np.floor(np.asarray(values) * (1 << r))
    if scaled.ndim == 0:
        scaled = scaled.reshape(1)
    if scaled.dtype == object or np.issubdtype(scaled.dtype, np.floating):
        integers = _convert_to_object_integers(scaled)
    else:
        integers = scaled.astype(object)
    return _saturate(integers, n)


def _saturate(mantissas: np.ndarray, n: int) -> np.ndarray:
    """Clip mantissas to the signed ``n``-bit range.

    Parameters
    ----------
    mantissas : numpy.ndarray
        Integer mantissas.
    n : int
        Signed width, including the sign bit.

    Returns
    -------
    numpy.ndarray
        Object array of Python integers in
        ``[-(2**(n - 1)), 2**(n - 1) - 1]``.
    """
    lower = -(1 << (n - 1))
    upper = (1 << (n - 1)) - 1
    clipped = np.clip(np.asarray(mantissas, dtype=object), lower, upper)
    if clipped.ndim == 0:
        clipped = clipped.reshape(1)
    return clipped


def _truncate_toward_zero(mantissas: np.ndarray, bits: int) -> np.ndarray:
    """Drop ``bits`` least-significant bits, truncating toward zero.

    Parameters
    ----------
    mantissas : numpy.ndarray
        Integer mantissas.
    bits : int
        How many low bits to drop. Zero returns ``mantissas``.

    Returns
    -------
    numpy.ndarray
        Truncated mantissas. Negative integers move toward zero, not toward
        ``-inf``.
    """
    if bits == 0:
        return mantissas
    divisor = 1 << bits
    negative = mantissas < 0
    magnitude = np.where(negative, -mantissas, mantissas)
    truncated = np.floor_divide(magnitude, divisor)
    return np.where(negative, -truncated, truncated)


class FixedPointArray:
    """An array of signed fixed-point values in format ``(n, r)``.

    Integer ``m`` is the real value ``m / 2**r``. Real inputs are floored
    toward negative infinity, then saturated to the signed ``n``-bit
    range. Addition and multiplication keep every result bit.
    :meth:`re_quantize` drops fractional bits toward zero and
    saturates. A right shift is arithmetic and does not change
    ``(n, r)``.
    """

    def __init__(self, values: Any, n: int = 16, r: int = 8) -> None:
        """Quantize real ``values`` into signed format ``(n, r)``.

        Parameters
        ----------
        values : array-like of float
            Real numbers. A scalar becomes a length-1 array.
        n : int, optional
            Signed width, including the sign bit. Default is 16.
        r : int, optional
            Fractional bit count. Default is 8.

        Raises
        ------
        ValueError
            If ``n`` is less than 1 or ``r`` is negative.
        """
        self._validate_format(n, r)
        self._n: int = int(n)
        self._r: int = int(r)
        self._mantissas: np.ndarray = _quantize(values, self._n, self._r)

    @classmethod
    def from_mantissas(
        cls, mantissas: Any, n: int, r: int
    ) -> FixedPointArray:
        """Build an array from integers that are already quantized.

        ``mantissas`` are numerators, not real values. Integer ``m``
        represents ``m / 2**r``. Integers outside the signed ``n``-bit
        range saturate. Use this when an earlier stage already produced
        fixed-point integers, instead of quantizing those integers as
        reals.

        Parameters
        ----------
        mantissas : int or array-like of int
            Integer numerators in format ``(n, r)``.
        n : int
            Signed width, including the sign bit. Must be at least 1.
        r : int
            Fractional bit count. Must be at least 0.

        Returns
        -------
        FixedPointArray
            Array of those integers in format ``(n, r)``. A scalar
            becomes a length-1 array.

        Raises
        ------
        TypeError
            If ``mantissas`` is not an integer or an integer array.
        ValueError
            If ``n`` or ``r`` is not a valid format.
        """
        cls._validate_format(n, r)
        integers = _convert_to_integer_array(mantissas)
        if integers.ndim == 0:
            integers = integers.reshape(1)
        width = int(n)
        fraction = int(r)
        return cls._create_array(_saturate(integers, width), width, fraction)

    @classmethod
    def _create_array(
        cls, mantissas: np.ndarray, n: int, r: int
    ) -> FixedPointArray:
        """Return an array that stores ``mantissas`` exactly.

        Parameters
        ----------
        mantissas : numpy.ndarray
            Object array of Python integers. A scalar is reshaped to
            length 1. Values must already fit in ``n`` bits.
        n : int
            Signed width.
        r : int
            Fractional bit count.

        Returns
        -------
        FixedPointArray
            Array viewing those integers in format ``(n, r)``.
        """
        integers = np.asarray(mantissas, dtype=object)
        if integers.ndim == 0:
            integers = integers.reshape(1)
        result = cls.__new__(cls)
        result._n: int = int(n)
        result._r: int = int(r)
        result._mantissas: np.ndarray = integers
        return result

    @classmethod
    def _create_exact_array(
        cls, mantissas: np.ndarray, n: int, r: int
    ) -> FixedPointArray:
        """Return an array, widening ``n`` until ``mantissas`` fit.

        Parameters
        ----------
        mantissas : numpy.ndarray
            Integer mantissas produced by an exact arithmetic step.
        n : int
            Smallest signed width the caller requires.
        r : int
            Fractional bit count of the result.

        Returns
        -------
        FixedPointArray
            Result whose width is ``max(n, width(mantissas))``.
        """
        integers = np.asarray(mantissas, dtype=object)
        width = max(int(n), _calculate_signed_width(integers))
        return cls._create_array(integers, width, int(r))

    @staticmethod
    def _validate_format(n: Any, r: Any) -> None:
        """Raise unless ``(n, r)`` is a signed fixed-point format.

        Parameters
        ----------
        n : int
            Signed width, including the sign bit.
        r : int
            Fractional bit count.

        Raises
        ------
        ValueError
            If ``n`` is less than 1 or ``r`` is negative.
        """
        if not isinstance(n, numbers.Integral) or n < 1:
            raise ValueError("n must be a positive integer")
        if not isinstance(r, numbers.Integral) or r < 0:
            raise ValueError("r must be a non-negative integer")

    @property
    def values(self) -> np.ndarray:
        """Return a copy of the integer mantissas.

        Returns
        -------
        numpy.ndarray
            ``int64`` when every integer fits in a signed 64-bit word, and an
            object array of Python integers otherwise. Mutating the copy
            does not change this array.
        """
        if _calculate_signed_width(self._mantissas) <= 64:
            return self._mantissas.astype(np.int64)
        return self._mantissas.copy()

    @property
    def n(self) -> int:
        """Return the signed mantissa width, including the sign bit.

        Returns
        -------
        int
            Width ``n``.
        """
        return self._n

    @property
    def r(self) -> int:
        """Return the fractional bit count.

        Returns
        -------
        int
            Fraction bits ``r``.
        """
        return self._r

    def get_quantization(self) -> tuple[int, int]:
        """Return the ``(n, r)`` format.

        Returns
        -------
        tuple of int
            ``(n, r)``.
        """
        return self._n, self._r

    def set_values(self, values: Any) -> None:
        """Replace the stored integers by quantizing real ``values``.

        The current ``(n, r)`` format is kept. Inputs are floored toward
        ``-inf`` and saturated.

        Parameters
        ----------
        values : array-like of float
            Real numbers. A scalar becomes a length-1 array.
        """
        self._mantissas = _quantize(values, self._n, self._r)

    def to_float(self) -> np.ndarray:
        """Return the represented real values.

        Returns
        -------
        numpy.ndarray
            ``mantissa / 2**r`` as floating-point numbers. Magnitudes
            above ``2**53`` can lose integer precision in float64.
        """
        scaled = np.asarray(self._mantissas, dtype=float)
        return scaled / (1 << self._r)

    def re_quantize(self, n: int, r: int) -> FixedPointArray:
        """Change this array's format in place and return it.

        Dropped fractional bits are truncated toward zero. Growing the
        fraction shifts mantissas left. Integers that do not fit in the new
        width saturate. The operand arrays passed to earlier operations
        are not affected because this updates only this array.

        Parameters
        ----------
        n : int
            Signed width of the new format.
        r : int
            Fractional bit count of the new format.

        Returns
        -------
        FixedPointArray
            This array, now in format ``(n, r)``.

        Raises
        ------
        ValueError
            If ``n`` or ``r`` is not a valid format.
        """
        self._validate_format(n, r)
        n = int(n)
        r = int(r)
        if r < self._r:
            mantissas = _truncate_toward_zero(self._mantissas, self._r - r)
        elif r > self._r:
            mantissas = self._mantissas * (1 << (r - self._r))
        else:
            mantissas = self._mantissas
        self._mantissas = _saturate(mantissas, n)
        self._n = n
        self._r = r
        return self

    def _add_fixed(self, other: FixedPointArray) -> FixedPointArray:
        """Add another fixed-point array at full precision.

        Parameters
        ----------
        other : FixedPointArray
            Array to add. Its shape must broadcast with this array.

        Returns
        -------
        FixedPointArray
            Sum. ``r`` is the larger fraction. ``n`` covers both aligned
            operands and one carry bit.
        """
        common_r = max(self._r, other._r)
        left = self._mantissas * (1 << (common_r - self._r))
        right = other._mantissas * (1 << (common_r - other._r))
        grown = max(
            self._n + (common_r - self._r),
            other._n + (common_r - other._r),
        ) + 1
        return self._create_exact_array(left + right, grown, common_r)

    def __add__(self, other: Any) -> Any:
        """Return the sum at full precision.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Fixed-point array, real integer, or array of real integers.
            Integers use this array's fractional width.

        Returns
        -------
        FixedPointArray or NotImplemented
            Sum, or ``NotImplemented`` when ``other`` is not supported.
            ``n`` grows to cover the operands. ``r`` is unchanged when
            ``other`` is an integer.
        """
        if isinstance(other, FixedPointArray):
            return self._add_fixed(other)
        if _is_integral_operand(other):
            total = self._mantissas + _calculate_scaled_integers(
                other, self._r
            )
            return self._create_exact_array(total, self._n, self._r)
        return NotImplemented

    def __radd__(self, other: Any) -> Any:
        """Return ``other + self``.

        Parameters
        ----------
        other : int or array-like of int
            Real integer on the left of the sum.

        Returns
        -------
        FixedPointArray or NotImplemented
            Same result as :meth:`__add__`.
        """
        return self.__add__(other)

    def __mul__(self, other: Any) -> Any:
        """Return the product at full precision.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Fixed-point array, or a dimensionless integer scale.

        Returns
        -------
        FixedPointArray or NotImplemented
            Product. Two fixed-point arrays use ``r`` equal to the sum of
            the input fractions and ``n`` at least the sum of the widths.
            An integer scale keeps ``r`` and grows ``n`` by the scale's
            signed width. ``NotImplemented`` when ``other`` is unsupported.
        """
        if isinstance(other, FixedPointArray):
            product = self._mantissas * other._mantissas
            return self._create_exact_array(
                product, self._n + other._n, self._r + other._r
            )
        if _is_integral_operand(other):
            integers = _convert_to_integer_array(other)
            product = self._mantissas * integers
            grown = self._n + _calculate_signed_width(integers)
            return self._create_exact_array(product, grown, self._r)
        return NotImplemented

    def __rmul__(self, other: Any) -> Any:
        """Return ``other * self``.

        Parameters
        ----------
        other : int or array-like of int
            Dimensionless integer scale on the left.

        Returns
        -------
        FixedPointArray or NotImplemented
            Same result as :meth:`__mul__`.
        """
        return self.__mul__(other)

    def __neg__(self) -> FixedPointArray:
        """Return the negation.

        Returns
        -------
        FixedPointArray
            Negated mantissas. ``r`` is unchanged. ``n`` grows when
            the most negative signed integer does not fit when negated.
        """
        return self._create_exact_array(-self._mantissas, self._n, self._r)

    def __sub__(self, other: Any) -> Any:
        """Return ``self - other`` at full precision.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Value to subtract. Integers are real values.

        Returns
        -------
        FixedPointArray or NotImplemented
            Difference, or ``NotImplemented`` when ``other`` is not
            supported.
        """
        if isinstance(other, FixedPointArray):
            return self + (-other)
        if _is_integral_operand(other):
            return self + (-_convert_to_integer_array(other))
        return NotImplemented

    def __rsub__(self, other: Any) -> Any:
        """Return ``other - self``.

        Parameters
        ----------
        other : int or array-like of int
            Real integer on the left.

        Returns
        -------
        FixedPointArray or NotImplemented
            Difference, or ``NotImplemented`` when ``other`` is not an
            integer operand.
        """
        if _is_integral_operand(other):
            return (-self) + other
        return NotImplemented

    def _shift(self, shift: Any, to_the_left: bool) -> FixedPointArray:
        """Shift mantissas, leaving the fractional width unchanged.

        Parameters
        ----------
        shift : int or array-like of int
            Non-negative shift counts. Must broadcast with this array.
        to_the_left : bool
            True shifts toward the MSB and grows ``n``. False is an
            arithmetic shift toward ``-inf`` and keeps ``n``.

        Returns
        -------
        FixedPointArray
            Shifted integers with the same ``r``.

        Raises
        ------
        ValueError
            If a shift count is negative or the shape does not broadcast.
        TypeError
            If ``shift`` is not an integer or an integer array.
        """
        shifts = _convert_to_integer_array(shift)
        if np.any(shifts < 0):
            raise ValueError("shift counts must be non-negative")
        operation = np.left_shift if to_the_left else np.right_shift
        try:
            shifted = operation(self._mantissas, shifts)
        except ValueError as error:
            raise ValueError(
                "shift counts must be broadcastable to the array"
            ) from error
        if to_the_left:
            extra = int(np.max(shifts)) if shifts.size else 0
            width = self._n + extra
        else:
            width = self._n
        return self._create_exact_array(shifted, width, self._r)

    def __lshift__(self, shift: Any) -> FixedPointArray:
        """Shift mantissas left by ``shift`` bits.

        Parameters
        ----------
        shift : int or array-like of int
            Non-negative shift counts.

        Returns
        -------
        FixedPointArray
            Shifted integers. ``r`` is unchanged and ``n`` grows by the
            largest shift count.

        Raises
        ------
        ValueError
            If a shift count is negative or the shape does not broadcast.
        TypeError
            If ``shift`` is not an integer or an integer array.
        """
        return self._shift(shift, True)

    def __rshift__(self, shift: Any) -> FixedPointArray:
        """Arithmetic-shift mantissas right by ``shift`` bits.

        Parameters
        ----------
        shift : int or array-like of int
            Non-negative shift counts.

        Returns
        -------
        FixedPointArray
            Shifted integers. Negative mantissas move toward ``-inf``.
            ``(n, r)`` is unchanged.

        Raises
        ------
        ValueError
            If a shift count is negative or the shape does not broadcast.
        TypeError
            If ``shift`` is not an integer or an integer array.
        """
        return self._shift(shift, False)

    def _align_operands(self, other: Any) -> tuple[np.ndarray, np.ndarray]:
        """Return mantissas of ``self`` and ``other`` at a common fraction.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Value to compare against.

        Returns
        -------
        tuple of numpy.ndarray
            ``(left, right)`` integer mantissas that can be compared
            directly.
        """
        if isinstance(other, FixedPointArray):
            common_r = max(self._r, other._r)
            left = self._mantissas * (1 << (common_r - self._r))
            right = other._mantissas * (1 << (common_r - other._r))
            return left, right
        return self._mantissas, _calculate_scaled_integers(other, self._r)

    def _compare(self, other: Any, operation: Any, unsupported: Any) -> Any:
        """Compare mantissas after aligning fractional widths.

        Parameters
        ----------
        other : object
            Candidate operand.
        operation : callable
            Elementwise NumPy comparison.
        unsupported : object
            Value returned when ``other`` is not a supported operand.

        Returns
        -------
        numpy.ndarray or object
            Boolean mask, or ``unsupported`` when ``other`` is not a
            fixed-point array or an integer operand.
        """
        if (
            not isinstance(other, FixedPointArray)
            and not _is_integral_operand(other)
        ):
            return unsupported
        left, right = self._align_operands(other)
        return operation(left, right)

    def __lt__(self, other: Any) -> Any:
        """Return a mask of where ``self < other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value. Fixed-point values are aligned to the larger
            fraction. Integers are real values.

        Returns
        -------
        numpy.ndarray or NotImplemented
            Elementwise mask, or ``NotImplemented`` if ``other`` is not
            supported.
        """
        return self._compare(other, np.less, NotImplemented)

    def __le__(self, other: Any) -> Any:
        """Return a mask of where ``self <= other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value.

        Returns
        -------
        numpy.ndarray or NotImplemented
            Elementwise mask, or ``NotImplemented`` if ``other`` is not
            supported.
        """
        return self._compare(other, np.less_equal, NotImplemented)

    def __gt__(self, other: Any) -> Any:
        """Return a mask of where ``self > other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value.

        Returns
        -------
        numpy.ndarray or NotImplemented
            Elementwise mask, or ``NotImplemented`` if ``other`` is not
            supported.
        """
        return self._compare(other, np.greater, NotImplemented)

    def __ge__(self, other: Any) -> Any:
        """Return a mask of where ``self >= other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value.

        Returns
        -------
        numpy.ndarray or NotImplemented
            Elementwise mask, or ``NotImplemented`` if ``other`` is not
            supported.
        """
        return self._compare(other, np.greater_equal, NotImplemented)

    def __eq__(self, other: Any) -> Any:
        """Return a mask of where ``self == other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value.

        Returns
        -------
        numpy.ndarray or bool
            Elementwise mask. ``False`` when ``other`` is not a supported
            operand.
        """
        return self._compare(other, np.equal, False)

    def __ne__(self, other: Any) -> Any:
        """Return a mask of where ``self != other``.

        Parameters
        ----------
        other : FixedPointArray or int or array-like of int
            Compared value.

        Returns
        -------
        numpy.ndarray or bool
            Elementwise mask. ``True`` when ``other`` is not a supported
            operand.
        """
        return self._compare(other, np.not_equal, True)

    def __getitem__(self, key: Any) -> FixedPointArray:
        """Return the selected entries in the same format.

        Parameters
        ----------
        key : int or slice or array-like
            Index passed through to the mantissa array.

        Returns
        -------
        FixedPointArray
            Selected integers. A scalar index becomes a length-1 array.
            ``(n, r)`` is unchanged.
        """
        selected = np.array(self._mantissas[key], dtype=object, copy=True)
        return self._create_exact_array(selected, self._n, self._r)

    def __setitem__(self, key: Any, value: Any) -> None:
        """Assign into the selected entries and saturate.

        Parameters
        ----------
        key : int or slice or array-like
            Index passed through to the mantissa array.
        value : FixedPointArray or int or array-like of int
            Fixed-point array with the same ``r``, or real integers that
            are quantized to this ``r``. Assigned integers saturate to ``n``.

        Raises
        ------
        ValueError
            If ``value`` is a fixed-point array with a different ``r``.
        TypeError
            If ``value`` is not a fixed-point array or integers.
        """
        if isinstance(value, FixedPointArray):
            if value.r != self._r:
                raise ValueError(
                    "assigned FixedPointArray must have matching r"
                )
            incoming = value._mantissas
        else:
            incoming = _calculate_scaled_integers(value, self._r)
        updated = self._mantissas.copy()
        incoming = np.asarray(incoming, dtype=object)
        destination = np.ndim(updated[key])
        if destination == 0:
            flat = np.reshape(incoming, -1)
            if flat.size != 1:
                raise ValueError(
                    "a scalar index requires one assigned element"
                )
            updated[key] = int(flat[0])
        else:
            updated[key] = incoming
        self._mantissas = _saturate(updated, self._n)

    def __iter__(self) -> Any:
        """Yield one array per index along the first axis.

        Yields
        ------
        FixedPointArray
            A row with the same ``(n, r)`` format. One-dimensional arrays
            yield length-1 arrays.
        """
        for row in self._mantissas:
            copied = np.array(row, dtype=object, copy=True)
            yield self._create_exact_array(copied, self._n, self._r)

    def __array__(
        self, dtype: Any = None, copy: bool | None = None
    ) -> np.ndarray:
        """Return integer mantissas for the NumPy array protocol.

        Parameters
        ----------
        dtype : data-type, optional
            Requested dtype. The default matches :attr:`values`.
        copy : bool or None, optional
            ``False`` is rejected because the stored buffer is not a
            numeric NumPy view. Any other value returns a new array.

        Returns
        -------
        numpy.ndarray
            Integer mantissas, not the real values.

        Raises
        ------
        ValueError
            If ``copy`` is False.
        """
        if copy is False:
            raise ValueError(
                "a FixedPointArray mantissa buffer cannot be viewed in place"
            )
        if dtype is None:
            return self.values
        return np.array(self.values, dtype=dtype, copy=True)

    def __repr__(self) -> str:
        """Return a constructor-style description of the real values.

        Returns
        -------
        str
            Text of the form ``FixedPointArray(..., n=n, r=r)``.
        """
        return f"FixedPointArray({self.to_float()}, n={self._n}, r={self._r})"


class FixedPointArrayTests(unittest.TestCase):
    """Tests for :class:`FixedPointArray` quantization and arithmetic."""

    def test_constructor_and_saturation(self) -> None:
        """Tests floor quantization and signed saturation."""
        value = FixedPointArray([-100, -1.25, 0.5, 100], n=8, r=4)
        np.testing.assert_array_equal(value.values, [-128, -20, 8, 127])
        self.assertEqual(value.get_quantization(), (8, 4))

    def test_addition_preserves_fractional_precision_and_grows_width(
        self,
    ) -> None:
        """Tests full-precision addition and integer addition."""
        left = FixedPointArray([1.25], n=8, r=2)
        right = FixedPointArray([0.125], n=8, r=3)
        result = left + right
        np.testing.assert_allclose(result.to_float(), [1.375])
        self.assertEqual(result.r, 3)
        self.assertGreaterEqual(result.n, 10)
        np.testing.assert_array_equal((left + 2).values, [13])

    def test_multiplication_preserves_all_product_bits(self) -> None:
        """Tests full-precision multiplication by arrays and integers."""
        left = FixedPointArray([1.25], n=8, r=2)
        right = FixedPointArray([-0.75], n=8, r=3)
        result = left * right
        np.testing.assert_allclose(result.to_float(), [-0.9375])
        self.assertEqual(result.get_quantization(), (16, 5))
        np.testing.assert_array_equal((left * np.array([2])).values, [10])
        self.assertEqual((left * 2).r, left.r)

    def test_reverse_arithmetic_and_subtraction(self) -> None:
        """Tests reflected addition and subtraction, and negation."""
        value = FixedPointArray([1.5, -0.5], n=8, r=2)
        np.testing.assert_allclose((2 + value).to_float(), [3.5, 1.5])
        np.testing.assert_allclose((3 - value).to_float(), [1.5, 3.5])
        np.testing.assert_allclose((-value).to_float(), [-1.5, 0.5])

    def test_requantize_truncates_and_saturates(self) -> None:
        """Tests narrowing the fraction and the width."""
        value = FixedPointArray([1.375, -1.375], n=16, r=3)
        value.re_quantize(4, 1)
        np.testing.assert_array_equal(value.values, [2, -2])
        self.assertEqual(value.get_quantization(), (4, 1))

    def test_requantize_truncates_negative_toward_zero(self) -> None:
        """Tests that dropped fraction bits move negatives toward zero."""
        value = FixedPointArray(-5 / 16, n=8, r=4)
        self.assertEqual(int(value.values[0]), -5)
        value.re_quantize(8, 2)
        self.assertEqual(int(value.values[0]), -1)
        self.assertEqual(value.get_quantization(), (8, 2))

    def test_shifts_operate_on_mantissas(self) -> None:
        """Tests left and right shifts of mantissas."""
        value = FixedPointArray([1.5, -1.5], n=8, r=2)
        left = value << 3
        right = value >> 1
        np.testing.assert_array_equal(left.values, [48, -48])
        self.assertEqual(left.r, value.r)
        self.assertGreaterEqual(left.n, value.n + 3)
        np.testing.assert_array_equal(right.values, [3, -3])
        self.assertEqual(right.get_quantization(), value.get_quantization())
        np.testing.assert_array_equal(value << np.array([1, 2]), [12, -24])

    def test_right_shift_of_negative_is_arithmetic(self) -> None:
        """Tests that a right shift rounds negative mantissas toward -inf."""
        value = FixedPointArray(-5 / 16, n=8, r=4)
        shifted = value >> 2
        self.assertEqual(int(shifted.values[0]), -2)
        self.assertEqual(shifted.get_quantization(), value.get_quantization())

    def test_comparisons_align_quantization_and_return_masks(self) -> None:
        """Tests comparison masks across different fractional widths."""
        left = FixedPointArray([0.5, 1.5, -1], n=8, r=2)
        right = FixedPointArray([0.25, 1.75, -1], n=8, r=3)
        np.testing.assert_array_equal(left < right, [False, True, False])
        np.testing.assert_array_equal(left > right, [True, False, False])
        np.testing.assert_array_equal(left == right, [False, False, True])
        np.testing.assert_array_equal(left >= 1, [False, True, False])

    def test_indexing_and_mask_assignment(self) -> None:
        """Tests indexing and masked assignment."""
        value = FixedPointArray([0.5, 1, 1.5], n=8, r=2)
        self.assertEqual(value[1].get_quantization(), value.get_quantization())
        value[value > 1] = FixedPointArray([2], n=8, r=2)
        np.testing.assert_allclose(value.to_float(), [0.5, 1, 2])
        value[0] = FixedPointArray([2], n=8, r=2)
        self.assertEqual(int(value.values[0]), 8)
        self.assertEqual(float(value.to_float()[0]), 2.0)

    def test_subtracts_integer_arrays(self) -> None:
        """Tests subtraction of integer lists and arrays."""
        value = FixedPointArray([1.5, -0.5, 0.25], n=8, r=2)
        difference = value - np.array([1, 0, -2])
        np.testing.assert_array_equal(difference.values, [2, -2, 9])
        self.assertEqual(difference.r, value.r)

    def test_from_mantissas_keeps_integers_and_saturates(self) -> None:
        """Tests construction from integers that are already quantized."""
        saturated = FixedPointArray.from_mantissas([8, -3], n=4, r=1)
        np.testing.assert_array_equal(saturated.values, [7, -3])
        self.assertEqual(saturated.get_quantization(), (4, 1))
        exact = FixedPointArray.from_mantissas([3], n=8, r=1)
        self.assertEqual(float(exact.to_float()[0]), 1.5)
        wide = FixedPointArray.from_mantissas([2**80], n=100, r=0)
        self.assertEqual(int(wide.values[0]), 2**80)

    def test_wide_product_does_not_wrap(self) -> None:
        """Tests that products wider than 64 bits stay exact."""
        value = FixedPointArray([1], n=8, r=0) << 40
        product = value * value
        self.assertEqual(int(product.values[0]), 2**80)
        self.assertGreaterEqual(product.n, _calculate_bit_width(2**80))

    def test_arithmetic_does_not_modify_operands(self) -> None:
        """Tests that arithmetic copies rather than updating inputs."""
        left = FixedPointArray([1.5, -0.5], n=8, r=2)
        right = FixedPointArray([0.25], n=8, r=3)
        before_left = left.values.copy()
        before_right = right.values.copy()
        _ = left + right
        _ = left * right
        _ = left << 1
        np.testing.assert_array_equal(left.values, before_left)
        np.testing.assert_array_equal(right.values, before_right)

    def test_rejects_non_integer_shifts_and_operands(self) -> None:
        """Tests rejection of fractional scales and negative shifts."""
        value = FixedPointArray([1], n=8, r=2)
        with self.assertRaises(TypeError):
            _ = value * 1.5
        with self.assertRaises(ValueError):
            _ = value << -1


def main() -> None:
    """Run the fixed-point unit tests."""
    unittest.main()


if __name__ == "__main__":
    main()

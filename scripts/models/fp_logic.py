'''
Alex Knowlton
10/24

Fixed point logic using numpy
'''

import numpy as np


def fp_quantize(x, n=16, r=8):
    '''
    Quantizes input x to mantissa values in Q(n,r) format of the same
    shape as x

    inputs:
    x - input numpy array/matrix
    n - number of bits overall, default 16
    r - number of fractional bits, default 8

    outputs:
    x_fp - quantized mantissa values of x
    '''
    if type(x) != type(np.array([1])):
        x = np.array([x])
    else:
        x = np.copy(x)
    upper_max = np.power(2, n - 1) - 1
    lower_max = -np.power(2, n - 1)
    x *= np.power(2, r)
    x = np.array(np.floor(x))

    is_over_max = x > upper_max
    is_under_min = x < lower_max
    x[is_over_max] = upper_max
    x[is_under_min] = lower_max
    return x.astype(int)


def fp_mult(x, y, n_x=16, n_y=16, r_x=8, r_y=8, n_z=16, r_z=8):
    '''
    Multiplies fixed-point arrays x and y in fixed point form
    and outputs z in fixed point
    Inputs:
    x - array 1
    y - array 2, must be same shape as x
    n_x - number of bits in x, default 16
    r_x - number of fractional bits in x, default 8
    n_y - number of bits in y, default 16
    r_x - number of fractional bits in y, default 8
    n_z - number of bits in output, default 16
    r_z - number of fractional bits in output, default 8

    Outputs:
    z: x * y quantized to Q(n_z, r_z)
    '''
    mantissa_prod = x * y  # product of mantissa values
    R_out = r_x + r_y
    N_out = n_x + n_y
    # now do fractional bit stuff
    # if Rout > R3, then we have more fractional bits than we want
    # but we need to shift by the difference to make mantissas work
    # so: Rout > R3, must right shift
    mantissa_prod = mantissa_prod / np.power(2, (R_out - r_z))
    mantissa_prod = np.array(np.floor(mantissa_prod))
    if n_z < N_out:
        # saturate
        max_value = np.power(2, n_z - 1) - 1
        min_value = -np.power(2, n_z - 1)
        is_over_max_value = mantissa_prod > max_value
        is_under_min_value = mantissa_prod < min_value
        mantissa_prod[is_over_max_value] = max_value
        mantissa_prod[is_under_min_value] = min_value
    return np.array(mantissa_prod, dtype=int)


def fp_add(x, y, n_x=16, n_y=16, r_x=8, r_y=8, n_z=16, r_z=8):
    '''
    Adds fixed-point arrays x and y in fixed point form
    and outputs z in fixed point. x and y must have the same shape.
    Inputs:
    x - array 1
    y - array 2
    n_x - number of bits in x, default 16
    r_x - number of fractional bits in x, default 8
    n_y - number of bits in y, default 16
    r_x - number of fractional bits in y, default 8
    n_z - number of bits in output, default 16
    r_z - number of fractional bits in output, default 8

    Outputs:
    z: x * y quantized to Q(n_z, r_z)
    '''
    diff = r_x - r_y
    if diff < 0:  # then shift x
        x *=  np.array(x) * np.power(2, -diff)
    else:
        y = np.array(y) * np.power(2, diff)
    r_out = np.max([r_x, r_y])
    z_out = x + y

    # now get to the correct number of bits
    z_out *= np.power(2, r_z - r_out)
    z_out = np.array(np.floor(z_out))  # truncate decimals
    upper_max = np.power(2, n_z - 1) - 1
    lower_max = -np.power(2, n_z - 1)
    is_over_max = z_out > upper_max
    is_under_min = z_out < lower_max
    z_out[is_over_max] = upper_max
    z_out[is_under_min] = lower_max
    return np.array(z_out, dtype=int)


if __name__ == '__main__':
    # self-test module when run
    a = 1.5345
    b = -2.12345
    # quantize to 3 integer, 5 fractional bits
    n_a = 16
    r_a = 7
    n_b = 8
    r_b = 4
    a_fp = fp_quantize(a, n_a, r_a)
    b_fp = fp_quantize(b, n_b, r_b)
    sum_fp = fp_add(a_fp, b_fp, n_a, n_b, r_a, r_b, 11, 9) / (2 ** 9)
    mult_fp = fp_mult(a_fp, b_fp, n_a, n_b, r_a, r_b, 8, 3) / (2 ** 3)

    # generate expected values
    mult = np.round(a * b, 4)
    add = np.round(a + b, 4)

    print(f'Quantization A: Expected {a}, Received {a_fp / (2**r_a)}')
    print(f'Quantization A: Expected {b}, Received {b_fp / (2**r_b)}')
    print(f'Multiplication: Expected: {mult}, Received {mult_fp}')
    print(f'Addition: Expected {add}, Received {sum_fp}')
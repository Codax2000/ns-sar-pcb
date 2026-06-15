'''
Alex Knowlton
10/24

defines a CORDIC object capable of hyperbolic or linear
rotation or vectoring.
'''

from fp_logic import *
import numpy as np
import pdb

class CORDIC:
    '''
    CORDIC object
    '''

    def __init__(self, n_rotations=16, n_x=16, r_x=8, n_z=16, r_z=8):
        '''
        Object constructor. Defines what fixed point representation this object
        will use in Q(n_x, r_x) notation. Also defines how many times a
        rotation will be performed, defaults to 15 rotations and Q(16,8)
        '''
        self._n_x = n_x
        self._r_x = r_x
        self._n_z = n_z
        self._r_z = r_z
        self._n_rotations = n_rotations

    def rotate(self, x, y, z, is_hyperbolic=False):
        '''
        rotates x, y, and z towards z = 0. If is_hyperbolic is True, uses the
        arctanh lookup values instead of the arctan values.

        Note: x, y, and z can be single values or arrays, but not matrices
        '''
        return self._cordic_rotate(x, y, z, False, is_hyperbolic)

    def vector(self, x, y, z, is_hyperbolic=False):
        '''
        rotates x, y, and z towards y = 0. If is_hyperbolic is True, uses the
        arctanh lookup values instead of the arctan values.

        Note: x, y, and z can be single values or arrays, but not matrices
        '''
        return self._cordic_rotate(x, y, z, True, is_hyperbolic)
    
    def _cordic_rotate(self, x, y, z, is_vectoring, is_hyperbolic):
        '''
        Internal unified CORDIC logic. rotates x, y, and z based on whether
        CORDIC is in vectoring or hyperbolic mode and returns x, y, and z
        matrices based on iterations of the CORDIC. The first row is the input
        as it is passed to the function. The second is post-glue logic,
        followed by n_rotations rows of each value after iteration j. The last
        row is after scaling by the appropriate value of K.
        '''
        x, y, z = self._fix_types(x, y, z)
        x_glue, y_glue, z_glue = self._glue_logic(x, y, z, is_vectoring)

        # create result arrays
        x_out = np.zeros((self._n_rotations + 3, x.shape[1]))
        y_out = np.zeros((self._n_rotations + 3, x.shape[1]))
        z_out = np.zeros((self._n_rotations + 3, x.shape[1]))
        sigma = np.zeros((self._n_rotations, x.shape[1]))
        x_out[0, :] = x[0, :]
        y_out[0, :] = y[0, :]
        z_out[0, :] = z[0, :]

        x_out[1, :] = x_glue[0, :]
        y_out[1, :] = y_glue[0, :]
        z_out[1, :] = z_glue[0, :]

        # rename for readability, now that things are saved
        x = x_out
        y = y_out
        z = z_out

        # set appropriate lookup table for the operation
        lut, K, index, m = self.get_rotation_constants(is_hyperbolic)
        for i in range(len(index)):
            j_current = index[i]
            if is_vectoring:
                filt = y[i+1, :] >= 0
            else:
                filt = z[i+1, :] < 0
            sigma[i, filt] = -1
            sigma[i, ~filt] = 1

            x[i+2, :] = x[i+1, :] - m * sigma[i, :] * y[i+1, :] * (2.0**(-j_current))
            y[i+2, :] = y[i+1, :] + sigma[i, :] * x[i+1, :] * (2.0**(-j_current))
            z[i+2, :] = z[i+1, :] - sigma[i, :] * lut[i]

        x[-1, :] = fp_mult(x[-2, :], K, self._n_x, self._n_x, self._r_x, \
                           self._r_x, self._n_x, self._r_x)
        y[-1, :] = fp_mult(y[-2, :], K, self._n_x, self._n_x, self._r_x, \
                           self._r_x, self._n_x, self._r_x)
        z[-1, :] = z[-2, :]
        sigma[sigma == 0] = -1
        return x, y, z, sigma
    
    def _glue_logic(self, x, y, z, is_vectoring):
        '''
        Shifts things to the right half plane as necessary
        '''
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        ppi, npi, ppi_half, npi_half = self.get_pi_constants()
        z_gt_pihalf = z > ppi_half
        z_lt_pihalf = z < npi_half
        if is_vectoring:
            filt1 = x < 0
            filt2 = (x < 0) & (y >= 0)
            filt3 = (x < 0) & (y < 0)
        else:
            filt1 = z_gt_pihalf | z_lt_pihalf
            filt2 = z_lt_pihalf
            filt3 = z_gt_pihalf
        z[filt2] = fp_add(z[filt2], ppi, self._n_z, self._n_z, self._r_z, \
                          self._r_z, self._n_z, self._r_z)
        z[filt3] = fp_add(z[filt3], npi, self._n_z, self._n_z, self._r_z, \
                          self._r_z, self._n_z, self._r_z)
        x[filt1] = -x[filt1]
        y[filt1] = -y[filt1]
        return x, y, z
    
    def _fix_types(self, x, y, z):
        if type(x) != type(np.zeros(1)):
            x = np.array([x])
        if type(y) != type(np.zeros(1)):
            y = np.array([y])
        if type(z) != type(np.zeros(1)):
            z = np.array([z])

        max_length = max([len(x), len(y), len(z)])
        broadcaster = np.zeros((1, max_length))
        x = x + broadcaster
        y = y + broadcaster
        z = z + broadcaster

        return x, y, z
    
    def get_rotation_constants(self, is_hyperbolic):
        '''
        Returns the fixed point K and LUT values as decimal mantissa values 
        for this CORDIC based on whether this is hyperbolic or not
        '''
        index = np.arange(self._n_rotations)
        m = 1
        lut = np.arctan(np.power(2.0, -index))

        if is_hyperbolic:
            m = -1
            index += 1
            extra_numbers = []
            extra = 4
            while(extra < self._n_rotations):
                extra_numbers.append(extra)
                extra = 3 * extra + 1
            extra = np.array(extra_numbers)
            index = np.concatenate((index, extra))
            index = np.sort(index)
            index = index[:self._n_rotations]
            lut = np.arctanh(np.power(2.0, -index))
        K = np.prod(np.sqrt(1 + m * np.power(2.0, -2*index)))
        K_fp = fp_quantize(1 / K, self._n_x, self._r_x)
        lut = fp_quantize(lut, self._n_z, self._r_z)
        return lut, K_fp, index, m

    def get_pi_constants(self):
        '''
        Returns pi, -pi, pi / 2, and -pi / 2 as fixed point constants
        '''
        ppi = fp_quantize(np.pi, self._n_z, self._r_z)
        npi = fp_quantize(-np.pi, self._n_z, self._r_z)
        ppi_half = fp_quantize(np.pi / 2, self._n_z, self._r_z)
        npi_half = fp_quantize(-np.pi / 2, self._n_z, self._r_z)
        return ppi, npi, ppi_half, npi_half

    def __str__(self):
        return f'CORDIC:\n\t{self._n_rotations} iterations\n\tX: Q({self._n_x}, {self._r_x})\n\tZ: Q({self._n_z}, {self._r_z})'
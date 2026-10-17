'''
Aditya Patel
7/26/26

File: Creating a CORDIC module that functions in rotation mode. Goal is to plot cos and output of CORDIC module on the same waveform.

Something that needs to be verified: 1. the magnitude of the inputs vectors. The reason is x_out, y_out, z_out are all declared as 16-bit fixed-point integers, works fine with input vector (1,0) but fails with (2,3) with Q(16,13)

Two fixes: 
1. Increase int16 to int32 but depends if hardware allows us to do that
2. Reduce the precision of Q-format. We can make it Q(16, 12).
'''

import numpy as np
import matplotlib.pyplot as plt
from fp_logic import *

# Constants/setup - function that builds your tan^-1(2^-j) lookup table for j = 0 --> 15

class CORDIC:

    # Q(n,r) = (16,13) for x, y
    # Q(n,r) = (16,11) for z (angle)

    ''' Excepts the runtime format values for the way x, y, and z should be stored.
        Since x and y are two coordinates of the same vector, their magnitudes will be the same,
        and therefore n_Y and r_y is unnecessary.
    '''
    def __init__(self, n_rotations=16, n_x=16, r_x=13, n_z=16, r_z=11):      

        self._n_x = n_x
        self._n_z = n_z
        self._r_x = r_x
        self._r_z = r_z
        self._n_rotations = n_rotations

    def build_lut (self):
        index = np.arange(self._n_rotations)
        lut = np.arctan(np.power(2.0, -index))
        return lut

    # converting pi values into Q format
    def get_pi_constants (self):

        ppi         = fp_quantize(np.pi, self._n_z, self._r_z)      # π
        npi         = fp_quantize(-np.pi, self._n_z, self._r_z)     # -π
        ppi_half    = fp_quantize((np.pi)/2, self._n_z, self._r_z)  # π/2
        npi_half    = fp_quantize((-np.pi)/2, self._n_z, self._r_z) # -π/2
        return ppi, npi, ppi_half, npi_half

    '''
    Problem: the angles can also be represented betwee ~(-pi/2, pi/2). 
    We want to be able to represent a full circle from (-pi, pi), so we have
    rotate the vector and adjust the angle theta accordingly.
    '''
    def _glue_logic(self, x, y, z):
        x = np.array(x)                        # numpy arrays are passed by referenceso any change in the function will change the original contents.
        y = np.array(y)                        
        z = np.array(z)
        # z_qtz = fp_quantize(z, self._n_z, self._r_z)

        ppi, npi, ppi_half, npi_half = self.get_pi_constants()

        filt2 = z < npi_half        # z < -π/2
        filt3 = z > ppi_half        # z > π/2
        filt1 = filt2 | filt3

        ''' Add π if z < -π/2, else if z > π/2, subtract π
        '''
        z[filt2] = fp_add(z[filt2], ppi, self._n_z, self._n_z, self._r_z, \
                            self._r_z, self._n_z, self._r_z)
        z[filt3] = fp_add(z[filt3], npi, self._n_z, self._n_z, self._r_z, \
                            self._r_z, self._n_z, self._r_z)
        x[filt1] = -x[filt1]        # bring the vector from Quad II or III into I or IV
        y[filt1] = -y[filt1]
        return x, y, z

    def iteration(self, x, y, z):
        ''' CORDIC Engine runnning iterations
        
        Parameters:
        x: int, float, or numpy.ndarray
            Raw x-coordinate values
        y: int, float, or numpy.ndarray
            Raw y-coordinate values
        z: int, float, or numpy.ndarray
            Raw z-coordinate values

        Reuturns:
        tuple of nump.ndarray
            Returns (x_out, y_out, z_out, sigma) where histories are tracked across execution rows
        
        
        '''
        x, y, z = self._fix_types_and_quantize(x, y, z)
        x_glue, y_glue, z_glue = self._glue_logic(x, y, z)

        K = fp_quantize(1/1.64676, self._n_x, self._r_x)

        x_length = x.shape[1]
        broadcaster = np.zeros((1, x_length))
        K = K + broadcaster
        print("K:", np.shape([K]))
        print("x:", np.shape([x]))
        # creating 2D result arrays, initialized to all 0
        # np.zeros format = (rows, columns). So rows = n_rotations (16) + 3 = 19 for
        # original inputs, glue logic values, 16 iterations, and final K scaled output

        x_out = np.zeros((self._n_rotations + 3, x.shape[1]), dtype=np.int32)    #x.shape[1] because it returns the horizontal width aka # columns of x array
        y_out = np.zeros((self._n_rotations + 3, x.shape[1]), dtype=np.int32)
        z_out = np.zeros((self._n_rotations + 3, x.shape[1]), dtype=np.int32)
        sigma_j = np.zeros((self._n_rotations, x.shape[1]), dtype=np.int32)
        
        # the original inputs without any modifications
        x_out[0, :] = x[0, :]
        y_out[0, :] = y[0, :]
        z_out[0, :] = z[0, :]

        # the glue logic values
        x_out[1, :] = x_glue[0, :]
        y_out[1, :] = y_glue[0, :]
        z_out[1, :] = z_glue[0, :]

        # 16 iterations
        index = np.arange(self._n_rotations)
        lut = self.build_lut()
        lut = fp_quantize(lut, self._n_z, self._r_z)
        
        for i in range(len(index)):
            j_current = index[i]

            filt = z_out[i+1, :] < 0
            sigma_j[i, filt] = -1
            sigma_j[i, ~filt] = 1

            x_out[i+2, :] = x_out[i+1, :] - (sigma_j[i, :] * y_out[i+1, :] >> j_current)
            y_out[i+2, :] = y_out[i+1, :] + (sigma_j[i, :] * x_out[i+1, :] >> j_current)
            z_out[i+2, :] = z_out[i+1, :] - (sigma_j[i, :] * lut[j_current])

            print(f"i:{i}, x:{x_out[i+2,0]/2**self._r_x:.4f}, y:{y_out[i+2,0]/2**self._r_x:.4f}, "      
                    f"z:{z_out[i+2,0]/2**self._r_z:.4f}, sigma:{sigma_j[i,0]}")

        x_out[-1, :] = fp_mult(x_out[-2, :], K, self._n_x, self._n_x, self._r_x, self._r_x, self._n_x, self._r_x)
        y_out[-1, :] = fp_mult(y_out[-2, :], K, self._n_x, self._n_x, self._r_x, self._r_x, self._n_x, self._r_x)
        z_out[-1, :] = z_out[-2, :]
        
        print(f"i: 18, x: {x_out[-1, :]}, y: {y_out[-1, :]}, z: {z_out[-1, :]}, sigma: {sigma_j[i, :]}")
        return x_out, y_out, z_out, sigma_j
        

    def _fix_types_and_quantize(self, x, y, z):

        if type(x) != type(np.array([1])):
            x = np.array([x])
        if type(y) != type(np.array([1])):
            y = np.array([y])
        if type(z) != type(np.array([1])):
            z = np.array([z])

        x = fp_quantize(x, self._n_x, self._r_x)
        y = fp_quantize(y, self._n_x, self._r_x)
        z = fp_quantize(z, self._n_z, self._r_z)

        max_length = max([len(x), len(y), len(z)])
        broadcaster = np.zeros((1, max_length))
        x = x + broadcaster
        y = y + broadcaster
        z = z + broadcaster

        return x , y, z


''' Testing: Sweep Angles and plot them to verify the CORDIC engine'''
my_cordic = CORDIC()

# x0 = 1
# y0 = 0

x02 = 2
y02 = 3

thetas = np.linspace(-np.pi, np.pi, 200)

# run the iteration
x_out, y_out, z_out, sigma_j = my_cordic.iteration(1, 0, thetas)
# x_out, y_out, z_out, sigma_j = my_cordic.iteration(1, 0, np.pi/4)
# x_out2, y_out2, z_out2, sigma_j2 = my_cordic.iteration(x02, y02, thetas)

#plot
cordic_cos = x_out[-1, :]
cordic_cos = cordic_cos / (2**my_cordic._r_x)
# cordic_mix_x = x_out2[-1, :]
# cordic_mix_y = y_out2[-1, :]
# cordic_mix_x = cordic_mix_x/ (2**my_cordic._r_x)
# cordic_mix_y = cordic_mix_y/ (2**my_cordic._r_x)


plt.plot(thetas, cordic_cos, label='CORDIC')        #compare the cordic computed cos against numpy's in-built cos
# plt.plot(thetas, cordic_mix_x, label='cordic mix x', color='blue')
# plt.plot(thetas, cordic_mix_y, label='cordic mix y', color='green')

plt.plot(thetas, np.cos(thetas), label='numpy cos', linestyle='dashed')
# plt.plot(thetas, 2*np.cos(thetas) - 3*np.sin(thetas), label='2cos-3sin', linestyle="dashed", color='red')
# plt.plot(thetas, 2*np.sin(thetas) + 3*np.cos(thetas), label='2sin+3cos', linestyle="dashed", color='brown')
# plt.plot(thetas, cordic_cos - np.cos(thetas), label='error', linestyle='dashdot')
plt.legend()
plt.savefig('cordic_2.png')
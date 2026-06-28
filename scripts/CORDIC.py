'''
Alex Knowlton
10/24

Defines a CORDIC object capable of hyperbolic or linear
rotation or vectoring.
'''

from fp_logic import *
import numpy as np
import matplotlib.pyplot as plt
import pdb

class CORDIC:
    """
    CORDIC (Coordinate Rotation Digital Computer) simulation object.

    Simulates hardware-accurate CORDIC operations using fixed-point arithmetic 
    configurations. Supports both rotation and vectoring modes across linear 
    and hyperbolic coordinate systems.
    """

    def __init__(self, n_rotations=16, n_x=16, r_x=8, n_z=16, r_z=8):
        """
        Initialize the CORDIC engine with specific fixed-point formats and iterations.

        Parameters
        ----------
        n_rotations : int, optional
            Number of iterations to perform during processing. Defaults to 16.
        n_x : int, optional
            Total word length (bit width) for X and Y channels. Defaults to 16.
        r_x : int, optional
            Number of fractional bits for X and Y channels. Defaults to 8.
        n_z : int, optional
            Total word length (bit width) for the Z (angle) channel. Defaults to 16.
        r_z : int, optional
            Number of fractional bits for the Z (angle) channel. Defaults to 8.
        """
        self._n_x = n_x
        self._r_x = r_x
        self._n_z = n_z
        self._r_z = r_z
        self._n_rotations = n_rotations

    def rotate(self, x, y, z, is_hyperbolic=False):
        """
        Perform CORDIC rotation mode, driving the angle tracking value z towards 0.

        Parameters
        ----------
        x : int, float, or numpy.ndarray
            Initial X-coordinate(s). Can be scalar or 1D array-like.
        y : int, float, or numpy.ndarray
            Initial Y-coordinate(s). Can be scalar or 1D array-like.
        z : int, float, or numpy.ndarray
            Initial angle(s) to rotate through. Can be scalar or 1D array-like.
        is_hyperbolic : bool, optional
            If True, performs hyperbolic rotation (using arctanh tables).
            If False, performs circular/linear rotation (using arctan tables). 
            Defaults to False.

        Returns
        -------
        x_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking X values across stages.
        y_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking Y values across stages.
        z_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking Z values across stages.
        sigma_history : numpy.ndarray
            Matrix of shape (n_rotations, N) containing rotation directions (-1 or 1).
        """
        return self._cordic_rotate(x, y, z, False, is_hyperbolic)

    def vector(self, x, y, z, is_hyperbolic=False):
        """
        Perform CORDIC vectoring mode, driving the Y-coordinate towards 0.

        Parameters
        ----------
        x : int, float, or numpy.ndarray
            Initial X-coordinate(s). Can be scalar or 1D array-like.
        y : int, float, or numpy.ndarray
            Initial Y-coordinate(s). Can be scalar or 1D array-like.
        z : int, float, or numpy.ndarray
            Initial accumulator angle(s). Can be scalar or 1D array-like.
        is_hyperbolic : bool, optional
            If True, performs hyperbolic vectoring. If False, performs 
            circular/linear vectoring. Defaults to False.

        Returns
        -------
        x_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking X values across stages.
        y_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking Y values across stages.
        z_history : numpy.ndarray
            Matrix of shape (n_rotations + 3, N) tracking Z values across stages.
        sigma_history : numpy.ndarray
            Matrix of shape (n_rotations, N) containing rotation directions (-1 or 1).
        """
        return self._cordic_rotate(x, y, z, True, is_hyperbolic)
    
    def _cordic_rotate(self, x, y, z, is_vectoring, is_hyperbolic):
        """
        Internal unified CORDIC engine executing execution loops and scaling adjustments.

        The output matrices contain structurally indexed rows:
          - Row 0: Original inputs.
          - Row 1: Outputs post quadrant-mapping correction (glue logic).
          - Rows 2 to (n_rotations + 1): State history per iteration step `j`.
          - Row -1 (Last): Final state scaled by the compensation factor `K`.

        Parameters
        ----------
        x : int, float, or numpy.ndarray
            Raw X-coordinate values.
        y : int, float, or numpy.ndarray
            Raw Y-coordinate values.
        z : int, float, or numpy.ndarray
            Raw Z-coordinate values.
        is_vectoring : bool
            Directs loop to track y=0 if True, else z=0 if False.
        is_hyperbolic : bool
            Selects hyperbolic lookup configurations and scaling constants if True.

        Returns
        -------
        tuple of numpy.ndarray
            Returns (x_out, y_out, z_out, sigma) where histories are tracked across 
            execution rows.
        """
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
        """
        Map target coordinates or angles into convergence-safe domains.
        """
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
        """
        Standardize raw parameter types and broadcast scalars/arrays into consistent matrices.
        """
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
        """
        Generate quantized step lookup vectors, scaling limits, and indices.
        """
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
        """
        Retrieve quantized boundary references based on Z register fixed-point settings.
        """
        ppi = fp_quantize(np.pi, self._n_z, self._r_z)
        npi = fp_quantize(-np.pi, self._n_z, self._r_z)
        ppi_half = fp_quantize(np.pi / 2, self._n_z, self._r_z)
        npi_half = fp_quantize(-np.pi / 2, self._n_z, self._r_z)
        return ppi, npi, ppi_half, npi_half

    def __str__(self):
        return f'CORDIC:\n\t{self._n_rotations} iterations\n\tX: Q({self._n_x}, {self._r_x})\n\tZ: Q({self._n_z}, {self._r_z})'


if __name__ == "__main__":
    # 1. Instantiate the CORDIC block with higher resolution for demo purposes
    # Using Q(24, 16) to ensure the fixed point logic handles pi/2 and 1.0 smoothly
    n_steps = 16
    cordic_engine = CORDIC(n_rotations=n_steps, n_x=24, r_x=16, n_z=24, r_z=16)
    
    # 2. Extract 1/K scale factor dynamically from your architecture constants
    _, K_reciprocal, _, _ = cordic_engine.get_rotation_constants(is_hyperbolic=False)
    
    # For a circular rotation to calculate sin(z) and cos(z):
    # x0 = 1/K, y0 = 0, z0 = target_angle
    initial_x = K_reciprocal
    initial_y = 0.0
    initial_z = np.pi / 2.0  # target angle
    
    # 3. Execute the CORDIC rotation engine
    x_hist, y_hist, z_hist, _ = cordic_engine.rotate(initial_x, initial_y, initial_z)
    
    # 4. Extract data array histories (flattening the matrix row shapes)
    # Rows 2 to (n_steps + 2) track values across the actual iteration indices 0 to n_steps-1
    iter_indices = np.arange(n_steps)
    x_iterations = x_hist[2:2 + n_steps, 0]
    y_iterations = y_hist[2:2 + n_steps, 0]
    z_iterations = z_hist[2:2 + n_steps, 0]
    
    print(f"Calculated Value for Sin(pi/2): {y_hist[-1, 0]:.6f} (Expected: ~1.0)")
    print(f"Calculated Value for Cos(pi/2): {x_hist[-1, 0]:.6f} (Expected: ~0.0)")

    # 5. Plotting configurations
    plt.figure(figsize=(10, 6))
    
    plt.plot(iter_indices, x_iterations, 'o-', label='X value (~Cos tracking)', color='crimson')
    plt.plot(iter_indices, y_iterations, 's-', label='Y value (~Sin tracking)', color='dodgerblue')
    plt.plot(iter_indices, z_iterations, '^--', label='Z angle error (rads)', color='orange')
    
    # Highlight final post-scaled adjustment row values
    plt.axhline(y=y_hist[-1, 0], color='blue', linestyle=':', alpha=0.6, label='Final Normalized Sin value')
    plt.axhline(y=x_hist[-1, 0], color='red', linestyle=':', alpha=0.6, label='Final Normalized Cos value')

    plt.title(f"CORDIC Converging States across {n_steps} Rotations ($\phi = \pi/2$)")
    plt.xlabel("Rotation Step Index ($j$)")
    plt.ylabel("Value State Magnitude")
    plt.xticks(iter_indices)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='best')
    plt.tight_layout()
    
    plt.savefig('./img/cordic_example.png')
========
Modeling
========

Python models of the fixed-point datapath, the CORDIC rotator, the sine-generator DAC, and the noise-shaping SAR. These pages are generated from the docstrings in ``scripts/models/``.

Fixed-point arrays
------------------

.. automodule:: models.fp_array
   :members:
   :special-members: __add__, __radd__, __mul__, __rmul__, __neg__, __sub__, __rsub__, __lshift__, __rshift__, __lt__, __le__, __gt__, __ge__, __eq__, __ne__, __getitem__, __setitem__, __iter__, __array__, __repr__
   :exclude-members: FixedPointArrayTests

CORDIC
------

.. automodule:: models.cordic
   :members:
   :exclude-members: CORDICTests

Sine-generator DAC
------------------

.. automodule:: models.sinegen_dac
   :members:
   :exclude-members: SineGenDACTests

Noise-shaping SAR
-----------------

.. automodule:: models.nssar
   :members:
   :exclude-members: NSSARTests

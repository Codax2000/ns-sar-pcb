"""Run a short noise-shaping SAR conversion.

Run from ``scripts/`` so the local imports resolve.
"""

import numpy as np

from nssar import convert_nssar


def main() -> None:
    """Convert one differential sine and print the table length."""
    n_samples = 128
    clocks = np.arange(n_samples)
    differential = 0.4 * np.cos(2.0 * np.pi * clocks / n_samples)
    vin_p = 0.5 + differential / 2.0
    vin_n = 0.5 - differential / 2.0
    results = convert_nssar(vin_p, vin_n, osr=16)
    print(f"Converted {len(results)} samples")


if __name__ == "__main__":
    main()

"""Async cocotb monitor for a DAC5311 SPI pin trio.

Protocol (MSB first, 16-bit frames):

- Falling SYNCb resets the in-flight shift register and bit count.
- Falling SCLK while SYNCb is low shifts DIN in.
- Rising SYNCb with fewer than 16 clocks discards the frame (e.g. reset
  abort). Rising SYNCb with 16 clocks appends one value: power bits
  [15:14], then unsigned code [13:6]. Power ``01`` stores ``-1``, ``10``
  stores ``-2``, ``00`` stores the code, and ``11`` fails the test.
"""

from __future__ import annotations

import cocotb
from cocotb.triggers import FallingEdge, First, RisingEdge, ValueChange


class Dac5311Monitor:
    """Observe one DAC5311 channel and collect decoded frame values."""

    def __init__(self, syncb, sclk, din) -> None:
        self._syncb = syncb
        self._sclk = sclk
        self._din = din
        self._values: list[int] = []
        cocotb.start_soon(self._run())

    def get_read_values(self) -> list[int]:
        """Return a copy of captured values since the last clear."""
        return list(self._values)

    def clear_read_values(self) -> None:
        """Drop captured values for the next stimulus window."""
        self._values.clear()

    async def wait_rising_syncb(self, count: int) -> None:
        """Wait for ``count`` rising edges on SYNCb."""
        for _ in range(count):
            await RisingEdge(self._syncb)

    async def _run(self) -> None:
        shreg = 0
        bit_count = 0
        while True:
            fall_sclk = FallingEdge(self._sclk)
            edge_syncb = ValueChange(self._syncb)
            fired = await First(fall_sclk, edge_syncb)
            if fired is edge_syncb:
                if int(self._syncb.value) == 0:
                    shreg = 0
                    bit_count = 0
                else:
                    if bit_count >= 16:
                        power = (shreg >> 14) & 0b11
                        code = (shreg >> 6) & 0xFF
                        if power == 0b01:
                            self._values.append(-1)
                        elif power == 0b10:
                            self._values.append(-2)
                        elif power == 0b00:
                            self._values.append(code)
                        else:
                            assert False, (
                                f"DAC5311 invalid power mode 0b{power:02b}"
                            )
                    shreg = 0
                    bit_count = 0
            elif int(self._syncb.value) == 0:
                shreg = ((shreg << 1) | (int(self._din.value) & 1)) & 0xFFFF
                bit_count += 1

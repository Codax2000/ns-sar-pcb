"""Stimulus for the bare ``spi`` module: one write, then one read.

Pin names match ``spi`` (``rst``, ``csb``). ``if_rd_data`` is driven
by hand so a following read can shift that value out on ``miso``. Check
write ``if_addr`` / ``if_wr_data`` in the waveform; the test only asserts
MISO readback of the hand-set data.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from utils.assertions import assert_equals
from utils.spi_utils import read_reg, write_reg

SYSCLK_PERIOD_NS = 8.33
SPI_ADDR = 6


@cocotb.test()
async def test_write_then_read(dut):
    """Write, then read back hand-driven ``if_rd_data`` on MISO."""
    cocotb.start_soon(Clock(dut.sysclk, SYSCLK_PERIOD_NS, unit="ns").start())

    dut.rst.value = 1
    dut.csb.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0
    dut.if_rd_data.value = 0x5AA5
    dut.if_rd_err.value = 0
    dut.if_wr_err.value = 0

    await ClockCycles(dut.sysclk, 8)
    dut.rst.value = 0
    await ClockCycles(dut.sysclk, 8)

    await write_reg(dut, SPI_ADDR, [0x1234])
    await ClockCycles(dut.sysclk, 16)
    got = await read_reg(dut, SPI_ADDR)
    assert_equals(
        got,
        [0x5AA5],
        f"MISO readback was 0x{got[0]:04X}, if_rd_data was 0x5AA5",
    )

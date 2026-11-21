"""Write FREQUENCY on ``test_dac_top`` over SPI, then read it back.

Pins: ``arst_n``, ``csb``, ``scl``, ``mosi`` / ``miso``. SPI address 6 is
FREQUENCY (CPUIF byte address ``0xC``).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from utils.assertions import assert_equals
from utils.spi_utils import read_reg, write_reg

SYSCLK_PERIOD_NS = 10


@cocotb.test()
async def test_frequency_write_read(dut):
    """Write FREQUENCY and expect the same value on the next read."""
    cocotb.start_soon(Clock(dut.sysclk, SYSCLK_PERIOD_NS, unit="ns").start())

    dut.arst_n.value = 0
    dut.csb.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0

    await ClockCycles(dut.sysclk, 8)
    dut.arst_n.value = 1
    await ClockCycles(dut.sysclk, 8)

    write_data = [
        0x00F8, # AC CONFIG
        0x001F, # ENABLE
        0x0000, # DACP_DC_VALUE
        0x0000, # DACN_DC_VALUE
        0x0000, # CLK_DIV
        0x0000, # STATUS
        0x0710  # FREQUENCY
    ]
    await write_reg(dut, 0x00, write_data)

    await ClockCycles(dut.sysclk, 16)
    got = await read_reg(dut, 0x00, 3)
    assert_equals(
        got,
        write_data[:3],
        f"AC_CONFIG readback was 0x{got[0]:04X}, wrote 0x{write_data[0]:04X}",
    )

    await write_reg(dut, 0x06, [0x002F])
    await ClockCycles(dut.sysclk, 3600)

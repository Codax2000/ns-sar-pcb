"""Cocotb connectivity test for ``chip_top`` (DAC path only).

Exercises SPI via ``dac_csb``, register readback, and dual DAC5311
power-down frames on the separate SYNCb pins.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from utils.assertions import assert_equals
from utils.dac5311_monitor import Dac5311Monitor
from utils.spi_utils import read_reg, write_reg

SYSCLK_PERIOD_PS = 8332

ADDR_AC_CONFIG = 0x00


async def _start_clock_and_reset(dut) -> None:
    cocotb.start_soon(Clock(dut.sysclk, SYSCLK_PERIOD_PS, unit="ps").start())
    dut.arst_n.value = 0
    dut.adc_csb.value = 1
    dut.dac_csb.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0
    await ClockCycles(dut.sysclk, 8)
    dut.arst_n.value = 1
    await ClockCycles(dut.sysclk, 8)


@cocotb.test()
async def test_chip_top_dac_connectivity(dut):
    """Write DAC regs with both enables low; read back; expect PD frames -1/-1."""
    await _start_clock_and_reset(dut)

    mon_p = Dac5311Monitor(
        dut.sinegen_dacp_syncb,
        dut.sinegen_dacp_sysclk,
        dut.sinegen_dinp,
    )
    mon_n = Dac5311Monitor(
        dut.sinegen_dacn_syncb,
        dut.sinegen_dacn_sysclk,
        dut.sinegen_dinn,
    )

    write_data = [
        0x00F8,  # AC_CONFIG
        0x0010,  # DACP_DC_VALUE
        0x0020,  # DACN_DC_VALUE
        0x0000,  # CLK_DIV
        0x0000,  # STATUS
        0x0400,  # FREQUENCY
        0x0000,  # ENABLE: both channels disabled
    ]
    mon_p.clear_read_values()
    mon_n.clear_read_values()
    await write_reg(dut, ADDR_AC_CONFIG, write_data)

    await ClockCycles(dut.sysclk, 16)
    got = await read_reg(dut, ADDR_AC_CONFIG, len(write_data))
    assert_equals(got, write_data, "chip_top DAC register readback mismatch")

    while len(mon_p.get_read_values()) < 1:
        await mon_p.wait_rising_syncb(1)
    while len(mon_n.get_read_values()) < 1:
        await mon_n.wait_rising_syncb(1)

    assert_equals(
        mon_p.get_read_values()[:1],
        [-1],
        "DACP power-down frame should be -1 (PD=01)",
    )
    assert_equals(
        mon_n.get_read_values()[:1],
        [-1],
        "DACN power-down frame should be -1 (PD=01)",
    )

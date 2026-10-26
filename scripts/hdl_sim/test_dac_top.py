"""Flat-pin check of the DAC subsystem top.

test_dac_top is the synthesizable DAC top: host SPI and the DAC5311
board pins. The stub holds SYNC inactive and SCLK and both DIN low.
No sine is generated and nothing here computes SNR.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


CLK_PERIOD_NS = 10


def drive_idle(dut):
    """Hold the host SPI quiet. Chip-select is active-low."""
    dut.csb.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0


def assert_dac_pins_idle(dut):
    """DAC5311 SYNC is active-low, so idle is high."""
    assert int(dut.sinegen_syncb.value) == 1
    assert int(dut.sinegen_sclk.value) == 0
    assert int(dut.sinegen_dinp.value) == 0
    assert int(dut.sinegen_dinn.value) == 0


@cocotb.test()
async def test_dac5311_pins_stay_idle(dut):
    """Serial pins stay at the serializer stub levels through reset."""
    dut.arst_n.value = 0
    drive_idle(dut)
    cocotb.start_soon(Clock(dut.sysclk, CLK_PERIOD_NS, unit="ns").start())
    await ClockCycles(dut.sysclk, 3)
    assert_dac_pins_idle(dut)

    dut.arst_n.value = 1
    await ClockCycles(dut.sysclk, 2)
    assert_dac_pins_idle(dut)

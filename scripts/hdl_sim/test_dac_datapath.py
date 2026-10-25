"""Tie-off checks for the dac_datapath skeleton.

Codes are 0 while rst_n is low and midscale (128) after reset. That
128 is the unsigned zero of generate_dac_values. dsm_locked stays 0.
No sine is generated and nothing here computes SNR.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


CLK_PERIOD_NS = 10
MIDSCALE = 0x80


def dsm_locked(dut):
    """Hardware writeback field inside hwif_in."""
    return int(dut.hwif_in.STATUS.dsm_locked.next.value)


@cocotb.test()
async def test_codes_are_zero_in_reset_and_midscale_after(dut):
    """DAC5311 codes and dsm_locked are constants, not a sine."""
    dut.rst_n.value = 0
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())
    await ClockCycles(dut.clk, 2)
    assert int(dut.dacp_value.value) == 0
    assert int(dut.dacn_value.value) == 0
    assert dsm_locked(dut) == 0

    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    assert int(dut.dacp_value.value) == MIDSCALE
    assert int(dut.dacn_value.value) == MIDSCALE
    assert dsm_locked(dut) == 0

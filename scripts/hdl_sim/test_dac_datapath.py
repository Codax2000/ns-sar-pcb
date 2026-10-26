"""Idle smoke test of the DAC datapath wrapper.

tb_dac_datapath flattens hwif_out onto plain ports and instantiates two
dac_5311 models. The serializer stub never starts a frame, so both real
outputs stay at midscale (code 128, 1.65 V at 3.3 V). rst_n is
active-low. This does not score a sine or an SNR.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


CLK_PERIOD_NS = 10
MIDSCALE_V = 128 * 3.3 / 256
TOL_V = 1e-6

FLAT_REGS = (
    "amplitude_scale",
    "amplitude",
    "dacp_enable",
    "dacp_mode",
    "dacn_enable",
    "dacn_mode",
    "dsm_enable",
    "dacp_dc_value",
    "dacn_dc_value",
    "clk_div_value",
    "dacp_power",
    "dacn_power",
    "frequency",
)


def drive_regs_zero(dut):
    for name in FLAT_REGS:
        getattr(dut, name).value = 0


def assert_midscale(dut):
    assert abs(float(dut.dacp_real.value) - MIDSCALE_V) < TOL_V
    assert abs(float(dut.dacn_real.value) - MIDSCALE_V) < TOL_V


@cocotb.test()
async def test_idle_outputs_stay_midscale(dut):
    """Both DAC voltages stay at midscale through and after reset."""
    dut.rst_n.value = 0
    drive_regs_zero(dut)
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())
    await ClockCycles(dut.clk, 2)
    assert_midscale(dut)

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert_midscale(dut)

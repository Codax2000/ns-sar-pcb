"""Idle smoke test of the DAC datapath wrapper.

tb_dac_datapath flattens hwif_out onto plain ports and instantiates two
dac_5311 models. The serializer stub never starts a frame, so both real
outputs stay at midscale (code 128, 1.65 V at 3.3 V). rst_n is
active-low. i_reg_write drives every swmod strobe; one pulse resets
the datapath for the following clock. This does not score a sine
or an SNR.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


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
    dut.i_reg_write.value = 0


def assert_midscale(dut):
    assert abs(float(dut.dacp_real.value) - MIDSCALE_V) < TOL_V
    assert abs(float(dut.dacn_real.value) - MIDSCALE_V) < TOL_V


def assert_sync_inactive(dut):
    """Reset state of the serializer: both active-low SYNC pins high."""
    assert dut.i_dac_datapath.o_syncb_dacp.value == 1
    assert dut.i_dac_datapath.o_syncb_dacn.value == 1


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


@cocotb.test()
async def test_reg_write_resets_datapath(dut):
    """A one-cycle register write resets the datapath for one clock."""
    dut.rst_n.value = 0
    drive_regs_zero(dut)
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    assert dut.i_dac_datapath.dp_rst_n.value == 1
    assert_sync_inactive(dut)
    assert_midscale(dut)

    # swmod is registered, so dp_rst_n falls on the cycle after the pulse.
    dut.i_reg_write.value = 1
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    assert dut.i_dac_datapath.dp_rst_n.value == 0
    assert_sync_inactive(dut)
    assert_midscale(dut)

    dut.i_reg_write.value = 0
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    assert dut.i_dac_datapath.dp_rst_n.value == 1
    assert_sync_inactive(dut)
    assert_midscale(dut)

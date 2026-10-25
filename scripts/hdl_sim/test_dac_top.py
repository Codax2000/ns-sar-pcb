"""Reset and CPUIF tie-off checks for the dac_top skeleton.

Codes sit at 0 while rst_n is low and at midscale (128) after reset.
That 128 is the unsigned zero of generate_dac_values. The CPUIF is a
one-word loopback at address 0, not dac_registers.rdl. No sine is
generated and nothing here computes SNR.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


CLK_PERIOD_NS = 10
MIDSCALE = 0x80


def drive_idle(dut):
    """Hold the passthrough CPUIF quiet."""
    dut.s_cpuif_req.value = 0
    dut.s_cpuif_req_is_wr.value = 0
    dut.s_cpuif_addr.value = 0
    dut.s_cpuif_wr_data.value = 0
    dut.s_cpuif_wr_biten.value = 0


async def start_clock_and_reset(dut):
    """Run sysclk and hold reset long enough for the loopback flops."""
    dut.rst_n.value = 0
    drive_idle(dut)
    cocotb.start_soon(Clock(dut.sysclk, CLK_PERIOD_NS, unit="ns").start())
    await ClockCycles(dut.sysclk, 2)


async def cpuif_access(dut, write, addr, data=0, biten=0xFFFF):
    """One passthrough access, accepted on a single rising edge.

    Read data is sampled after that edge's nonblocking update. Request
    is dropped on the following falling edge so it is not accepted twice.
    """
    await RisingEdge(dut.sysclk)
    dut.s_cpuif_req.value = 1
    dut.s_cpuif_req_is_wr.value = int(write)
    dut.s_cpuif_addr.value = addr
    dut.s_cpuif_wr_data.value = data
    dut.s_cpuif_wr_biten.value = biten
    await RisingEdge(dut.sysclk)
    await ReadOnly()
    rd_data = int(dut.s_cpuif_rd_data.value)
    rd_err = int(dut.s_cpuif_rd_err.value)
    wr_err = int(dut.s_cpuif_wr_err.value)
    await FallingEdge(dut.sysclk)
    dut.s_cpuif_req.value = 0
    return rd_data, rd_err, wr_err


@cocotb.test()
async def test_codes_are_zero_in_reset_and_midscale_after(dut):
    """DAC5311 codes are a tie-off, not a function of the CPUIF."""
    await start_clock_and_reset(dut)
    assert int(dut.dacp_value.value) == 0
    assert int(dut.dacn_value.value) == 0

    dut.rst_n.value = 1
    await RisingEdge(dut.sysclk)
    assert int(dut.dacp_value.value) == MIDSCALE
    assert int(dut.dacn_value.value) == MIDSCALE

    _, _, wr_err = await cpuif_access(dut, write=True, addr=0, data=0x00A5)
    assert wr_err == 0
    assert int(dut.dacp_value.value) == MIDSCALE
    assert int(dut.dacn_value.value) == MIDSCALE


@cocotb.test()
async def test_cpuif_loopback_is_address_zero_only(dut):
    """Writes at address 0 read back. Any other address is an error."""
    await start_clock_and_reset(dut)
    dut.rst_n.value = 1
    await RisingEdge(dut.sysclk)

    _, _, wr_err = await cpuif_access(
        dut, write=True, addr=0, data=0xABCD, biten=0xFFFF
    )
    assert wr_err == 0
    rd_data, rd_err, _ = await cpuif_access(dut, write=False, addr=0)
    assert rd_err == 0
    assert rd_data == 0xABCD

    _, _, wr_err = await cpuif_access(
        dut, write=True, addr=0, data=0x0012, biten=0x00FF
    )
    assert wr_err == 0
    rd_data, rd_err, _ = await cpuif_access(dut, write=False, addr=0)
    assert rd_err == 0
    assert rd_data == 0xAB12

    _, rd_err, wr_err = await cpuif_access(
        dut, write=True, addr=0x2, data=0xFFFF
    )
    assert wr_err == 1
    rd_data, rd_err, _ = await cpuif_access(dut, write=False, addr=0x2)
    assert rd_err == 1
    assert rd_data == 0
    rd_data, rd_err, _ = await cpuif_access(dut, write=False, addr=0)
    assert rd_err == 0
    assert rd_data == 0xAB12

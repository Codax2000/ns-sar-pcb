"""Cocotb tests for ``test_dac_top``: SPI registers and DAC5311 pin capture.

Pins: ``arst_n``, ``csb``, ``scl``, ``mosi`` / ``miso``, plus sinegen DAC
outputs. Buffered settings take effect when ENABLE is written.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from models.sinegen_dac import generate_dac_values

from utils.assertions import assert_equals
from utils.dac5311_monitor import Dac5311Monitor
from utils.spi_utils import read_reg, write_reg

SYSCLK_PERIOD_PS = 8332
N_SAMPLES = 100

ADDR_AC_CONFIG = 0x00
ADDR_ENABLE = 0x06


def _ac_config(amplitude_div_linear: int = 8, amplitude_div_log: int = 15) -> int:
    return (amplitude_div_log & 0xF) << 4 | (amplitude_div_linear & 0xF)


def _enable_word(
    *,
    dacp_enable: bool = True,
    dacp_ac: bool = True,
    dacn_enable: bool = True,
    dacn_ac: bool = True,
    dsm_enable: bool = False,
) -> int:
    return (
        (1 if dacp_enable else 0)
        | ((1 if dacp_ac else 0) << 1)
        | ((1 if dacn_enable else 0) << 2)
        | ((1 if dacn_ac else 0) << 3)
        | ((1 if dsm_enable else 0) << 4)
    )


async def _start_clock_and_reset(dut) -> None:
    cocotb.start_soon(Clock(dut.sysclk, SYSCLK_PERIOD_PS, unit="ps").start())
    dut.arst_n.value = 0
    dut.csb.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0
    await ClockCycles(dut.sysclk, 8)
    dut.arst_n.value = 1
    await ClockCycles(dut.sysclk, 8)


def _attach_monitors(dut) -> tuple[Dac5311Monitor, Dac5311Monitor]:
    mon_p = Dac5311Monitor(
        dut.u_dac_datapath.o_syncb_dacp,
        dut.sinegen_sclk,
        dut.sinegen_dinp,
    )
    mon_n = Dac5311Monitor(
        dut.u_dac_datapath.o_syncb_dacn,
        dut.sinegen_sclk,
        dut.sinegen_dinn,
    )
    return mon_p, mon_n


async def flash_dac_config(
    dut,
    *,
    frequency: int,
    amplitude_div_linear: int = 8,
    amplitude_div_log: int = 15,
    dacp_dc_value: int = 0,
    dacn_dc_value: int = 0,
    dacp_enable: bool = True,
    dacp_ac: bool = True,
    dacn_enable: bool = True,
    dacn_ac: bool = True,
    dsm_enable: bool = False,
) -> None:
    """Write buffered registers, then ENABLE so they take effect."""
    await write_reg(
        dut,
        ADDR_AC_CONFIG,
        [
            _ac_config(amplitude_div_linear, amplitude_div_log),
            dacp_dc_value & 0xFF,
            dacn_dc_value & 0xFF,
            0x0000,
            0x0000,
            frequency & 0xFFFF,
            _enable_word(
                dacp_enable=dacp_enable,
                dacp_ac=dacp_ac,
                dacn_enable=dacn_enable,
                dacn_ac=dacn_ac,
                dsm_enable=dsm_enable,
            )
        ],
    )


async def capture_dac_output(
    mon_p: Dac5311Monitor,
    mon_n: Dac5311Monitor,
    wait_mon: Dac5311Monitor,
    n_samples: int = N_SAMPLES,
) -> tuple[list[int], list[int]]:
    mon_p.clear_read_values()
    mon_n.clear_read_values()
    await wait_mon.wait_rising_syncb(n_samples)
    return mon_p.get_read_values(), mon_n.get_read_values()


@cocotb.test()
async def test_frequency_write_read(dut):
    """Write FREQUENCY and expect the same value on the next read."""
    await _start_clock_and_reset(dut)

    write_data = [
        0x00F8,  # AC CONFIG
        0x0000,  # DACP_DC_VALUE
        0x0000,  # DACN_DC_VALUE
        0x0000,  # CLK_DIV
        0x0000,  # STATUS
        0x0710,  # FREQUENCY
        0x001F,  # ENABLE
    ]
    await write_reg(dut, ADDR_AC_CONFIG, write_data)

    await ClockCycles(dut.sysclk, 16)
    got = await read_reg(dut, ADDR_AC_CONFIG, 3)
    assert_equals(
        got,
        write_data[:3],
        f"AC_CONFIG readback was 0x{got[0]:04X}, wrote 0x{write_data[0]:04X}",
    )

    await write_reg(dut, ADDR_ENABLE, [0x002F, 0x001F])
    await ClockCycles(dut.sysclk, 3600)


@cocotb.test()
async def test_frequency_sweep(dut):
    """Sweep 3 frequencies; each runs for 100 SYNCb rises vs the model."""
    await _start_clock_and_reset(dut)
    mon_p, mon_n = _attach_monitors(dut)

    amplitude_div_linear = 8
    amplitude_div_log = 15
    frequencies = [0x0100, 0x0400, 0x0710]

    for frequency in frequencies:
        await flash_dac_config(
            dut,
            frequency=frequency,
            amplitude_div_linear=amplitude_div_linear,
            amplitude_div_log=amplitude_div_log,
            dacp_ac=True,
            dacn_ac=True,
        )
        got_p, got_n = await capture_dac_output(mon_p, mon_n, mon_p)
        ref = generate_dac_values(
            len(got_p),
            frequency=frequency,
            amplitude_div_linear=amplitude_div_linear,
            amplitude_div_log=amplitude_div_log,
            dsm_enable=False,
            dacp_mode="AC",
            dacn_mode="AC",
        )
        assert_equals(
            got_p,
            list(ref["dacp_value"]),
            f"DACP mismatch at frequency 0x{frequency:04X}",
        )
        assert_equals(
            got_n,
            list(ref["dacn_value"]),
            f"DACN mismatch at frequency 0x{frequency:04X}",
        )


@cocotb.test()
async def test_amplitude_sweep(dut):
    """Sweep 3 amplitudes; each runs for 100 SYNCb rises vs the model."""
    await _start_clock_and_reset(dut)
    mon_p, mon_n = _attach_monitors(dut)

    frequency = 0x0400
    amplitude_div_linear = 8
    amplitude_div_logs = [15, 12, 8]

    for amplitude_div_log in amplitude_div_logs:
        await flash_dac_config(
            dut,
            frequency=frequency,
            amplitude_div_linear=amplitude_div_linear,
            amplitude_div_log=amplitude_div_log,
            dacp_ac=True,
            dacn_ac=True,
        )
        got_p, got_n = await capture_dac_output(mon_p, mon_n, mon_p)
        ref = generate_dac_values(
            len(got_p),
            frequency=frequency,
            amplitude_div_linear=amplitude_div_linear,
            amplitude_div_log=amplitude_div_log,
            dsm_enable=False,
            dacp_mode="AC",
            dacn_mode="AC",
        )
        assert_equals(
            got_p,
            list(ref["dacp_value"]),
            f"DACP mismatch at amplitude_div_log {amplitude_div_log}",
        )
        assert_equals(
            got_n,
            list(ref["dacn_value"]),
            f"DACN mismatch at amplitude_div_log {amplitude_div_log}",
        )


@cocotb.test()
async def test_ac_dc_mode(dut):
    """DACP AC and DACN DC; compare captured codes to the fixed-point model."""
    await _start_clock_and_reset(dut)
    mon_p, mon_n = _attach_monitors(dut)

    frequency = 0x0400
    amplitude_div_linear = 8
    amplitude_div_log = 15
    dacn_dc_value = 0x40

    await flash_dac_config(
        dut,
        frequency=frequency,
        amplitude_div_linear=amplitude_div_linear,
        amplitude_div_log=amplitude_div_log,
        dacn_dc_value=dacn_dc_value,
        dacp_ac=True,
        dacn_ac=False,
        dacn_enable=True,
    )
    got_p, got_n = await capture_dac_output(mon_p, mon_n, mon_p)
    ref = generate_dac_values(
        len(got_p),
        frequency=frequency,
        amplitude_div_linear=amplitude_div_linear,
        amplitude_div_log=amplitude_div_log,
        dsm_enable=False,
        dacp_mode="AC",
        dacn_mode="DC",
        dacn_dc_value=dacn_dc_value,
    )
    assert_equals(got_p, list(ref["dacp_value"]), "DACP AC mismatch")
    assert_equals(
        got_n,
        list(ref["dacn_value"]),
        f"DACN DC mismatch, expected constant 0x{dacn_dc_value:02X}",
    )

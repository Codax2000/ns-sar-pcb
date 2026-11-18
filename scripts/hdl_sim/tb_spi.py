"""Stimulus for the bare ``spi`` module: one write, then one read.

Pin names match ``spi`` (``rst_n``, ``cs_b``). ``if_rd_data`` is driven
by hand so a following read can shift that value out on ``miso``. Check
write ``if_addr`` / ``if_wr_data`` in the waveform; the test only asserts
MISO readback of the hand-set data.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

SYSCLK_PERIOD_NS = 8.33
SPI_HALF_PERIOD_NS = 100
SPI_ADDR = 6


def spi_frame(read: bool, addr: int, data: int = 0) -> list[int]:
    """Four-byte frame: command word, then write data or read dummies."""
    command = (0x8000 if read else 0) | (addr & 0x7FFF)
    return [
        (command >> 8) & 0xFF,
        command & 0xFF,
        (data >> 8) & 0xFF,
        data & 0xFF,
    ]


async def send_spi(dut, mosi_bytes: list[int]) -> list[int]:
    """Clock one SPI mode 0 frame on ``spi`` pins; return MISO bytes."""
    received: list[int] = []
    dut.scl.value = 0
    dut.cs_b.value = 1
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    dut.cs_b.value = 0

    for tx_byte in mosi_bytes:
        rx_byte = 0
        for bit_index in range(7, -1, -1):
            dut.mosi.value = (tx_byte >> bit_index) & 1
            await Timer(SPI_HALF_PERIOD_NS, unit="ns")
            dut.scl.value = 1
            await Timer(SPI_HALF_PERIOD_NS, unit="ns")
            rx_byte = (rx_byte << 1) | int(dut.miso.value)
            dut.scl.value = 0
        received.append(rx_byte)

    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    dut.cs_b.value = 1
    dut.mosi.value = 0
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    return received


@cocotb.test()
async def test_write_then_read(dut):
    """Write, then read back hand-driven ``if_rd_data`` on MISO."""
    cocotb.start_soon(Clock(dut.sysclk, SYSCLK_PERIOD_NS, unit="ns").start())

    dut.rst_n.value = 0
    dut.cs_b.value = 1
    dut.scl.value = 0
    dut.mosi.value = 0
    dut.if_rd_data.value = 0x5AA5
    dut.if_rd_err.value = 0
    dut.if_wr_err.value = 0

    await ClockCycles(dut.sysclk, 8)
    dut.rst_n.value = 1
    await ClockCycles(dut.sysclk, 8)

    await send_spi(dut, spi_frame(False, SPI_ADDR, 0x1234))
    await ClockCycles(dut.sysclk, 16)
    miso = await send_spi(dut, spi_frame(True, SPI_ADDR))
    got = (miso[2] << 8) | miso[3]
    assert got == 0x5AA5, (
        f"MISO readback was 0x{got:04X}, if_rd_data was 0x5AA5"
    )

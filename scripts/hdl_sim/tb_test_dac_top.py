"""Write FREQUENCY on ``test_dac_top`` over SPI, then read it back.

Pins: ``arst_n``, ``csb``, ``scl``, ``mosi`` / ``miso``. SPI address 6 is
FREQUENCY (CPUIF byte address ``0xC``).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

SYSCLK_PERIOD_NS = 10
SPI_HALF_PERIOD_NS = 100
SPI_ADDR_FREQUENCY = 6
WRITE_DATA = 0x1234


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
    """Clock one SPI mode 0 frame; return MISO bytes."""
    received: list[int] = []
    dut.scl.value = 0
    dut.csb.value = 1
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    dut.csb.value = 0

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
    dut.csb.value = 1
    dut.mosi.value = 0
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    return received


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

    await send_spi(dut, spi_frame(False, SPI_ADDR_FREQUENCY, WRITE_DATA))
    await ClockCycles(dut.sysclk, 16)
    miso = await send_spi(dut, spi_frame(True, SPI_ADDR_FREQUENCY))
    got = (miso[2] << 8) | miso[3]
    assert got == WRITE_DATA, (
        f"FREQUENCY readback was 0x{got:04X}, wrote 0x{WRITE_DATA:04X}"
    )

"""Write a DAC register over SPI and read it back.

The DUT is ``test_dac_top``. SPI address 6 is FREQUENCY: the block
keeps only ``if_addr[2:0]`` and appends a 0, so the CPUIF byte address
is ``0xC``. The frame is mode 0, MSB first: one command word
``{read, addr[14:0]}`` then one 16-bit data word. Read data is shifted
out during that second word.

Readback is expected to fail until the SPI clock-domain crossing holds
the register read data for the shift register. This test does not
change the RTL.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tb_test_dac_top import send_spi

SYSCLK_PERIOD_NS = 10
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

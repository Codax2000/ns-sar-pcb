"""Cocotb helpers for the host SPI register interface.

Drives ``dut.csb``, ``dut.scl``, ``dut.mosi``, and samples ``dut.miso``
in SPI mode 0. Frames match ``spi``: a 16-bit command word (R/W + 15-bit
address), then one or more 16-bit data words while CS stays low.
"""

from cocotb.triggers import Timer

SPI_HALF_PERIOD_NS = 100


def _word_bytes(word: int) -> list[int]:
    return [(word >> 8) & 0xFF, word & 0xFF]


def _command_bytes(read: bool, address: int) -> list[int]:
    command = (0x8000 if read else 0) | (address & 0x7FFF)
    return _word_bytes(command)


async def _send_spi(dut, mosi_bytes: list[int]) -> list[int]:
    """Clock one SPI mode 0 burst; return MISO bytes."""
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


def _bytes_to_words(payload: list[int]) -> list[int]:
    words: list[int] = []
    for i in range(0, len(payload), 2):
        words.append((payload[i] << 8) | payload[i + 1])
    return words


async def write_reg(dut, address: int, data: list[int]) -> None:
    """Burst-write 16-bit words starting at ``address``."""
    mosi_bytes = _command_bytes(False, address)
    for word in data:
        mosi_bytes.extend(_word_bytes(word))
    await _send_spi(dut, mosi_bytes)


async def read_reg(dut, address: int, n_reads: int = 1) -> list[int]:
    """Burst-read ``n_reads`` 16-bit words starting at ``address``."""
    mosi_bytes = _command_bytes(True, address)
    mosi_bytes.extend([0] * (2 * n_reads))
    miso_bytes = await _send_spi(dut, mosi_bytes)
    return _bytes_to_words(miso_bytes[2:])

"""SPI master helper for the ``test_dac_top`` pins.

``test_dac_top`` exposes ``csb``, ``scl``, ``mosi``, ``miso``, and
``miso_en``. This module drives the first three and samples ``miso``.
``miso_en`` is the output-enable for the chip pin; ``test_dac_top``
does not tri-state ``miso``, so the helper reads ``miso`` directly.
"""

from cocotb.triggers import Timer

# SPI mode 0 at 1 MHz, same rate as the UVM SPI driver's default.
SPI_HALF_PERIOD_NS = 500


def _as_byte(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"SPI byte must be an int, got {value!r}")
    if value < 0 or value > 255:
        raise ValueError(f"SPI byte out of range 0..255: {value}")
    return value


def _sample_bit(signal) -> int:
    """1 when the pin is a solid 1. X and Z read as 0."""
    return 1 if str(signal.value) == "1" else 0


async def send_spi(dut, mosi_bytes: list[int]) -> list[int]:
    """Clock one full-duplex SPI frame and return the MISO bytes.

    SPI mode 0 on ``test_dac_top``: CPOL=0, CPHA=0. ``csb`` is active
    low and ``scl`` idles low. Bits are MSB first. Each MOSI bit is
    set up while SCL is low; the matching MISO bit is sampled while
    SCL is high, before the falling edge. One call is one chip-select
    frame. The returned list has one byte per entry of ``mosi_bytes``.
    """
    payload = [_as_byte(byte) for byte in mosi_bytes]
    if not payload:
        return []

    received: list[int] = []
    dut.scl.value = 0
    dut.csb.value = 1
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    dut.csb.value = 0

    for tx_byte in payload:
        rx_byte = 0
        for bit_index in range(7, -1, -1):
            dut.mosi.value = (tx_byte >> bit_index) & 1
            await Timer(SPI_HALF_PERIOD_NS, unit="ns")
            dut.scl.value = 1
            await Timer(SPI_HALF_PERIOD_NS, unit="ns")
            rx_byte = (rx_byte << 1) | _sample_bit(dut.miso)
            dut.scl.value = 0
        received.append(rx_byte)

    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    dut.csb.value = 1
    dut.mosi.value = 0
    await Timer(SPI_HALF_PERIOD_NS, unit="ns")
    return received

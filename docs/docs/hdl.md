# Digital Logic

ADCs need digital logic. This means a register interface for CSRs (control and status registers) and a main state machine to control the conversion. It therefore means closing timing and rigorous verification.

## Digital Architecture

The digital architecture is mainly a SPI interface that connects to a state machine. The state machine manages the NFFT conversion using control/status registers from the SPI clock domain and writes data from the SAR ADC to the data memory, which can be read from the SPI domain.

![Toplevel Architecture](./img/digital.png)

The incremental filters are implemented as simple up-counters, since they have a reset.

![Digital Filters](./img/dig_filter.png)

### Main State Machine

Most SAR ADCs are controlled via an asynchronous control loop an discrete clocking logic. This is not so easy with an FPGA, and short of building it with discrete components, it's easier to use an FSM. It should be fast enough to operate with no issues. The main state machine looks like so:

![Main State Machine](./img/main_state_machine.png)

This ADC will support noise-shaping and oversampling. The goal of the main state machine is to take a certain number of samples with the easiest possible controls; this controls the memory, oversampling, and clocking logic.

The ADC has the following values controllable via SPI:

- Incremental mode enable/disable
- DEM enable/disable
- Number of FFT samples (NFFT)
- Oversampling ratio (OSR)
- SHA/Integration length and overlap times
- The number of bits in the SAR quantizer

### SPI Protocol

SPI works in SPI mode 0, with a 15-bit address, which accesses 2 bytes at a time. That way, even though the RTL accesses using
a 16-bit address, SPI still works with 15 bit, and just retrieves the registers at address and address + 1, from
the RTL point of view. In other words, the address is the 15 MSBs of a 16-bit address, and the SPI interface just reads back two data words.

The SDO pin is tri-stated unless it is actively sending data.

For a write:

![SPI Write](./img/spi_write.png)

For a read:

![SPI Read](./img/spi_read.png)

It also supports burst read and write, with the address incrementing by 1 after each byte.

![SPI Burst Write](./img/spi_burst_write.png)

![SPI Burst Read](./img/spi_burst_read.png)


## Verification

Verification for this device will be done with UVM, using a combination of AXI and SPI.
The goal is to drive stimulus using an AXI agent to gain confidence that the RTL will
work, and repurpose a SPI agent to check the buses for shift registers and DACs.

### ADC Testbench

The ADC testbench is meant as a learning opportunity for UVM and also for a thorough testbench for the ADC RTL. Unlike a real tapeout, we can recompile, but I'd rather not.

![Digital Testbench](./img/uvm_tb.png)

### AXI Integration Testbench

If possible, I will integrate this with the Zynq PS such that this can be run similar to PYNQ. In that case, 
an AXI to SPI adapter will be necessary, and will be run like so:

The first thing to do will be to add an AXI adapter so that it can be used to communicate with both the DAC and the ADC.

![AXI to SPI](./img/axi_integration_tb.png)

## Integration

There are two options for integration. The first would be to integrate this with the
Zynq PS so that I can run AXI commands natively, like so:

![Zynq Validation](./img/zynq_validation_setup.png)

Given that my board very likely has a fried Ethernet chip, this may be difficult. If that
persists and I am not able to find a workaround, I will ignore the dedicated PS and use
the FPGA fabric only, using a Jupyter notebook over `pyserial`, with Arduino drivers
instead of Linux ones. The bonus is that the PCB design will remain the same.

![Arduino Validation](./img/arduino_validation_setup.png)


# Noise-Shaping SAR PCB
The goal of this project is to create a 2nd-order, noise shaping SAR on a printed circuit board (PCB).
This has several goals:
1) Understand, design, and build a mixed-signal PCB using SMD components
1) Go through the process of FPGA design and synthesis, including asynchronous RTL design
1) Become better at reading datasheets for discrete components
1) Build a UVM testbench that includes real-number modeling.
1) Using IEEE SystemRDL to describe a register model.
1) Design an analog/mixed-signal circuit using LTSpice, instead of my usual Spectre.
1) Implement a system that includes some kind of bus communication protocol, likely i2c or SPI.

## Architecture
This PCB follows the Silva-Steensgard architecture detailed in [1], shown below:

![Silva-Steensgard ADC](./img/silva_steensgard_architecture.png)

The quantizer is implemented as a 4-bit SAR ADC with redundancy to reduce quantization noise. This introduces a number of design challenges, the main ones being:
1) The SAR ADC requires a multi-tail comparator, which will have to be implemented 
2) The feedback DAC requires several bits, which are most easily sent from the FPGA with discrete shift registers, instead of buying an FPGA with more IO pins.

## Controls
By using control registers, it will be possible to set several things about the ADC:
1) The oversampling rate (OSR), which is only applicable for incremental mode
2) The total number of analysis samples (nfft)
3) Whether the ADC is in incremental or continous mode
4) The clock division ratio (dividing down from a master clock in the FPGA)
5) Turning DEM on and off
6) The number of 'warmup' samples
7) The 2nd-order filter coefficients for continuous mode

The controls and communication will be done via I2C. This means the setting of the control registers, beginning ADC operation, reading control registers, and reading data.

## Design
The digital side of the ADC, including communication and potentially clocking, is implemented on an FPGA. However, this design is meant to imitate a tapeout, so industry standard verification methodology is used, as far as free or open-source tools are available. This will include SystemVerilog real number modeling (SV-RNM) of the analog core. This is also an opportunity to do a deep-dive into Universal Verification Methodology (UVM). Therefore, the design process is as follows:
| Step | Tool |
| :--- | :--- |
| Initial Modeling | Python |
| Digital Logic Design | Xilinx Vivado |
| Analog SV Model | Xilinx Vivado |
| UVM Testbench | Xilinx Vivado |
| Analog Design | LTSpice |
| PCB Design | Altium Designer/KiCAD |
| Analog Verification | LTSpice/Altium |
| PCB Testing | Arduino/Electrical Test Bench |
| Analysis | Python |
| Documentation | Microsoft Office Online |

### Initial Block Diagram
The analog circuitry is on the left, and the digital on the right. The digital logic has all the control logic and the digital filters both for continuous mode and for incremental mode. It also has the storage and communication logic that will communicate directly with the tester, since the terminations are already handled.

![Block Diagram](./img/block_diagram.png)


## Python Simulation
The Python simulation shows an SNR of over 40 dB. This is discounting mismatch
noise, but DWA is shown to significantly reduce harmonics introduced by
capacitor mismatch, which is significant on discrete components.

![IADC Simulation](./img/dwa_compare.png)

This is with a single stage IADC.

## Verification Environment
The UVM verification environment consists of 3 UVCs:
1) Analog Input: UVM-MS only agent that can drive a single value or a sine wave. Since it will never
be operated in passive mode, the standard UVM principles are relaxed, i.e. the monitor will "know"
in which mode it is being operated. It shall be in single-ended or differential, so must be
configurable with supply voltage.
2) Bus interface: Either SPI or I2C. Must be register-compatible, that is, have additional support
for a register layer (adapter, additional subscribers/packet splitters, etc.)
3) Clock/reset: The FPGA will be supplied via a crystal oscillator, but reset should be internal.
Therefore, there is a single clock agent with single-ended or differential clocks.

### UVM Testcases
| Testcase Name | Purpose | Procedure |
| :--- | :--- | :--- |
| `test_reg_access` | Test that registers write and read correctly | Write a register, then read it back. The values should match. This  |
| `test_input_values` | Test that individual values are converted correctly | Generate `NFFT` random values and convert them, check that they match within the specified ENOB (effective number of bits). |

### Analog Simulation
It will be necessary to show that the analog frontend matches the SV-RNM model. This will be the focus of the analog design and simulation.
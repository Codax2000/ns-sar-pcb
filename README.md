# Noise-Shaping SAR PCB
The goal of this project is to create a 2nd-order, noise shaping SAR on a printed circuit board (PCB). The reasoning is to understand the architecture and the circuit design, since the performance will not come close to an integrated circuit (IC).

## Architecture
This PCB follows the Silva-Steensgard architecture detailed in [1], shown below:

![Silva-Steensgard ADC](./img/silva_steensgard_architecture.png)

The quantizer is implemented as a 3-bit SAR ADC to reduce quantization noise. This introduces a number of design challenges, the main ones being:
1) The SAR ADC generally requires a dual-tail comparator, so the comparator may have to be made of discrete transistors instead of using a comparator IC.
2) The feedback DAC will must rotated using DEM.

Due to issues with speed and the number of samples for a continuous-mode ADC, the DEM and potential limitations with memory also means adding an option within the architecture for incremental mode. This will reduce the required number of samples for meaningful data, since continuous ADCs require a warmup before the noise shaping becomes visible.

## Controls
By using control registers, it will also be possible to set several things about the ADC:
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
| PCB Design | Altium Designer |
| Analog Verification | LTSpice/Altium |
| PCB Testing | Arduino/Electrical Test Bench |
| Analysis | Python |
| Documentation | Microsoft Office Online |

### Initial Block Diagram
The analog circuitry is on the left, and the digital on the right. The digital logic has all the control logic and the digital filters both for continuous mode and for incremental mode. It also has the storage and communication logic that will communicate directly with the tester, since the terminations are already handled.

![Block Diagram](./img/block_diagram.png)

## Python Simulation
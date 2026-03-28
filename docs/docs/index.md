# PCB Design for a Noise-Shaping SAR

This has several goals:

1. Understand, design, and build a mixed-signal PCB using SMD components
1. Go through the process of FPGA design and synthesis, including asynchronous RTL design
1. Become better at reading datasheets for discrete components
1. Build a UVM testbench that includes real-number modeling.
1. Using IEEE SystemRDL to describe a register model.
1. Design an analog/mixed-signal circuit using LTSpice, instead of my usual Spectre.
1. Implement a system that includes some kind of bus communication protocol, likely I2C or SPI.

## Theory
TODO: insert simulations here

## ADC Architecture

The ADC will use a Silva-Steensgard topology with optional reset for incremental operation.

![Silva-Steensgard Topology](./img/adc_loop.png)

This should give fine results on a PCB while also presenting a decent challenge for this project.

## Technology

The ultimate goal of this is to add the PCB onto a Zynq dev board with the form factor of an Arduino shield. The goal there would be to have an all-in-one testbench, where the Zynq would act as signal generator, test prober (using onboard ADCs) and the digital part of the DUT, while also running Python in Linux for easy interaction with the board. In lieu of that, the same should be possible using an Arduino as the testbed, but the bringup would potentially be more difficult.

Here is a summary of the technology used:

| Purpose | Program |
| :--- | :--- |
| System Design | Python `numpy`, `scipy`, `matplotlib` |
| Documentation | Python `mkdocs` |
| Technical Diagrams | Python `schemdraw` |
| Digital Logic Design | Xilinx Vivado |
| Analog Circuit Design | LTSpice, NGSpice |
| PCB Design | KiCAD |


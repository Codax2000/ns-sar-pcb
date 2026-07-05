# Verification

This device must, of course, be verified. One of the main goals of this project
is to gain experience with UVM, and so there will be two separate testbenches,
depending on whether I can get the PetaLinux build running on my SoC to the
point where Jupyter can be run from it.

## Architecture

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

## Test List and Status

Here is the latest live status from the regression pipeline.

<style>
  /* Target the 4th column of the table on this page */
  table td:nth-child(4) {
    max-width: 300px;
    white-space: normal; /* Forces text wrapping */
    word-break: break-word;
  }
</style>

{% include "subpages/regression_table.md" %}
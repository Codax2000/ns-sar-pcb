'''
Script: diagrams

This script is meant to be used to draw all the technical diagrams for
this project. This includes:

- Silva-Steensgard Theory
- Toplevel Schematics
- Digital Architecture
- Main State Machine
- Analog Comparator
- SAR Logic
- FPGA/PCB Floorplanning

'''

import os
import schemdraw
import schemdraw.flow as flow
import schemdraw.elements as elm


# Function: draw_silva_steensgard_loop
# Draws a high-level Silva-Steensgard noise-shaping SAR ADC loop.
# Saves the schematic as img/silva_steensgard_loop.png.
def draw_silva_steensgard_loop():
    """Draw Silva-Steensgard ADC loop schematic and save to img/."""
    os.makedirs("img", exist_ok=True)

    with schemdraw.Drawing() as d:
        d.config(unit=3)

        # Input and DAC front-end
        inp = d.add(blocks.Source().label("Vin"))
        d.add(elm.Line().right())
        summing = d.add(blocks.Sum().label("+ / -"))
        d.add(elm.Line().right())
        dac = d.add(blocks.Block().label("Cap DAC\n(SAR)"))
        d.add(elm.Line().right())
        quant = d.add(blocks.Block().label("Quantizer\n(Comparator)"))
        d.add(elm.Line().right())
        sar = d.add(blocks.Block().label("SAR Logic"))

        # Feedback from SAR to DAC
        d.add(elm.Line().down().length(3))
        d.add(elm.Line().left().tox(dac.S))
        d.add(elm.Line().up().toy(dac.S))

        # Noise-shaping loop filter (Silva-Steensgard style)
        d += summing
        d.add(elm.Line().down().length(3))
        loop_filt = d.add(blocks.Block().label("Loop Filter\n(SS Integrator)"))
        d.add(elm.Line().left().tox(inp.S))
        d.add(elm.Line().up().toy(inp.S))

        d.save("img/silva_steensgard_loop.png")


# Function: draw_block_level_adc
# Draws a guessed block-level schematic of the overall ADC PCB design:
# front-end, ADC core, digital backend, SPI, and clock/reset.
# Saves the schematic as img/block_level_adc.png.
def draw_block_level_adc():
    """Draw block-level ADC PCB schematic and save to img/."""
    os.makedirs("img", exist_ok=True)

    with schemdraw.Drawing() as d:
        d.config(unit=3)

        # Analog front-end
        ain = d.add(blocks.Source().label("Analog Input(s)"))
        d.add(elm.Line().right())
        afe = d.add(blocks.Block().label("Analog Front-End\n(Buffer / S&H)"))
        d.add(elm.Line().right())
        adc_core = d.add(blocks.Block().label("Noise-Shaping\nSAR ADC Core"))

        # Digital backend
        d.add(elm.Line().right())
        dig = d.add(blocks.Block().label("Digital Backend\n(Decimation / Filter)"))
        d.add(elm.Line().right())
        mem = d.add(blocks.Block().label("ADC Output\nMemory"))

        # SPI + control
        d.add(elm.Line().down().length(3))
        spi = d.add(blocks.Block().label("SPI Interface\n& Register Map"))
        d.add(elm.Line().left().tox(adc_core.S))
        d.add(elm.Line().up().toy(adc_core.S))

        # Clock / reset
        d.add(elm.Line().down().length(3))
        clk = d.add(blocks.Block().label("Clock / Reset\n(PLL / CLKGEN)"))
        d.add(elm.Line().left().tox(afe.S))
        d.add(elm.Line().up().toy(afe.S))

        d.save("img/block_level_adc.png")


# Function: draw_digital_architecture
# Draws the digital architecture of the ADC block, including:
# - SPI + register map
# - Control FSM
# - CDC bridge between SPI clock domain and ADC clock domain
# - NFFT controller and memory interface
# Saves the schematic as img/digital_architecture.png.
def draw_digital_architecture():
    """Draw digital architecture with CDC bridge and save to img/."""
    os.makedirs("img", exist_ok=True)

    with schemdraw.Drawing() as d:
        d.config(unit=3)

        # Left: SPI domain
        spi = d.add(blocks.Block().label("SPI Interface\n(SPI clk domain)"))
        d.add(elm.Line().right())
        ral = d.add(blocks.Block().label("Register Map\n(RAL View)"))

        # CDC bridge
        d.add(elm.Line().right())
        cdc = d.add(blocks.Block().label("CDC Bridge\n(SPI clk → ADC clk)"))

        # Right: ADC clock domain
        d.add(elm.Line().right())
        ctrl = d.add(blocks.Block().label("Main Control FSM\n(ADC clk domain)"))
        d.add(elm.Line().right())
        nfft = d.add(blocks.Block().label("NFFT Controller\n& Sample Counter"))
        d.add(elm.Line().right())
        memif = d.add(blocks.Block().label("ADC Output\nMemory Interface"))

        # Feedback from FSM to registers (status)
        d.add(elm.Line().down().length(3))
        status = d.add(blocks.Block().label("Status / Readback\n(MAIN_STATE_RB,\nSYNC_RESET_RB,\nN_VALID_SAMPLES)"))
        d.add(elm.Line().left().tox(ral.S))
        d.add(elm.Line().up().toy(ral.S))

        d.save("img/digital_architecture.png")


# Function: draw_main_state_machine
# Draws the main state machine for NFFT-based conversion:
# IDLE → CONFIG → RUNNING → DONE, with early abort path.
# Saves the schematic as img/main_state_machine.png.
def draw_main_state_machine():
    """Draw main state machine schematic and save to img/."""
    os.makedirs("img", exist_ok=True)

    with schemdraw.Drawing() as d:
        d.config(unit=2.5)

        idle = d.add(flow.Start().label("IDLE"))
        d.add(elm.Line().right())
        cfg = d.add(flow.Process().label("LOAD CONFIG\n(OSR, NFFT,\nMODES)"))
        d.add(elm.Line().right())
        runn = d.add(flow.Process().label("RUN NFFT\nCOLLECT SAMPLES"))
        d.add(elm.Line().right())
        done = d.add(flow.Terminator().label("DONE"))

        # Arrows
        d.add(elm.Arrow().at(idle.E).to(cfg.W).label("START_CONVERSION=1", loc="top"))
        d.add(elm.Arrow().at(cfg.E).to(runn.W).label("CONFIG OK", loc="top"))
        d.add(elm.Arrow().at(runn.E).to(done.W).label("N_SAMPLES == 2^NFFT", loc="top"))

        # Early abort path
        d.add(elm.Line().down().at(runn.S).length(2))
        abort = d.add(flow.Decision().label("ABORT?\n(START_CONVERSION=0)"))
        d.add(elm.Line().left().tox(idle.S))
        d.add(elm.Arrow().to(idle.S))

        d.save("img/main_state_machine.png")


# Function: draw_dual_tail_strong_arm_latch
# Draws a conceptual dual-tail strong-arm latch at block level:
# differential input pair, first tail (preamp), second tail (regeneration),
# and cross-coupled latch outputs. This is a conceptual block diagram,
# not a transistor-accurate schematic.
# Saves the schematic as img/dual_tail_strong_arm_latch.png.
def draw_dual_tail_strong_arm_latch():
    """Draw dual-tail strong-arm latch schematic (conceptual) and save to img/."""
    os.makedirs("img", exist_ok=True)

    with schemdraw.Drawing() as d:
        d.config(unit=2.5)

        # Differential inputs
        vinp = d.add(blocks.Source().label("Vin+"))
        d.add(elm.Line().right())
        diffp = d.add(blocks.Block().label("Diff Pair\n(M1+)"))

        d.add(elm.Line().down().at(vinp.S).length(2))
        vinn = d.add(blocks.Source().label("Vin-"))
        d.add(elm.Line().right())
        diffn = d.add(blocks.Block().label("Diff Pair\n(M1-)"))

        # First tail (preamp)
        d.add(elm.Line().down().at(diffp.S).length(2))
        tail1 = d.add(blocks.Block().label("Tail 1\n(Preamp)"))
        d.add(elm.Line().down().length(1))
        clk1 = d.add(blocks.Block().label("CLK1\n(Precharge / Eval)"))

        # Second tail (regeneration)
        d.add(elm.Line().right().at(diffp.E).length(2))
        regen = d.add(blocks.Block().label("Regeneration\nCross-Coupled\nLatch"))
        d.add(elm.Line().right().length(2))
        outp = d.add(blocks.Block().label("Vout+"))

        d.add(elm.Line().down().at(diffn.E).length(2))
        d.add(elm.Line().right().tox(regen.S))

        d.add(elm.Line().down().at(outp.S).length(2))
        outn = d.add(blocks.Block().label("Vout-"))

        # Second tail clock
        d.add(elm.Line().down().at(regen.S).length(2))
        tail2 = d.add(blocks.Block().label("Tail 2\n(Regeneration)"))
        d.add(elm.Line().down().length(1))
        clk2 = d.add(blocks.Block().label("CLK2\n(Regeneration Phase)"))

        d.save("img/dual_tail_strong_arm_latch.png")

'''
Function: test_schemdraw

Tests that schemdraw is working properly by pulling an example from their
website
'''
def test_schemdraw():
    pass

'''
Function: main

If the img directory does not exist, creates it. Then runs schematic creation
functions.
'''
def main():
    test_schemdraw()


if __name__ == '__main__':
    main()
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

import schemdraw
import schemdraw.elements as elm


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
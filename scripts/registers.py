'''
Script: registers.py

Generates the following outputs:

DAC registers (AXI4-Lite, on-fabric):
  - RTL via peakrdl-regblock with AXI4-Lite CPUIF

ADC registers + conversion memory (SPI passthrough, external device):
  - RTL via peakrdl-regblock with passthrough CPUIF
  - Clock-domain synchronizer RTL

Unified chip_top (DAC + ADC composed):
  - UVM register package (single RAL model covering both sub-maps)
  - HTML documentation (top-level only)
'''

import sys
import argparse
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl_uvm import UVMExporter
from peakrdl_html import HTMLExporter
from peakrdl_regblock import RegblockExporter
from peakrdl_regblock.cpuif.passthrough import PassthroughCpuif
from peakrdl_regblock.cpuif.axi4lite import AXI4Lite_Cpuif
from peakrdl_regblock.udps import ALL_UDPS
from synchronizer_exporter import RTLSyncExporter
from peakrdl_cheader.exporter import CHeaderExporter


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

# RDL source files
DEFAULT_UDP_RDL_SPEC  = './hdl_design/hdl_design.srcs/registers/regblock_udps.rdl'
DEFAULT_DAC_RDL_SPEC  = './hdl_design/hdl_design.srcs/registers/dac_registers.rdl'
DEFAULT_ADC_RDL_SPEC  = './hdl_design/hdl_design.srcs/registers/adc_registers.rdl'
DEFAULT_TOP_RDL_SPEC  = './hdl_design/hdl_design.srcs/registers/chip_top.rdl'

# HTML documentation directory (top-level only)
DEFAULT_TOP_HTML_PATH = './docs/docs/chip_top'

# UVM register package (generated from chip_top for the full RAL model)
DEFAULT_UVM_PKG_PATH  = \
    './hdl_design/hdl_design.srcs/dv/axi_top_env/chip_regs_dv_pkg.sv'

# RTL output directories (one per independently compiled block)
DEFAULT_DAC_RTL_PATH  = './hdl_design/hdl_design.srcs/rtl/registers/dac'
DEFAULT_ADC_RTL_PATH  = './hdl_design/hdl_design.srcs/rtl/registers/adc'

# ADC register synchronizer output file
DEFAULT_REG_SYNC_PATH = \
    './hdl_design/hdl_design.srcs/rtl/registers/adc/adc_reg_sync.sv'

# C header output file (generated from chip_top for software driver use)
DEFAULT_CHEADER_PATH = \
    './software/firmware/src/registers/chip_top_registers.h'

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_input_arguments():
    '''
    Function: parse_input_arguments

    Parse keyword arguments. Use

    --- Code
    python registers.py --help
    ---

    for full usage.
    '''
    parser = argparse.ArgumentParser(
        description='Generate RTL, UVM, and HTML from PeakRDL register specs.')

    parser.add_argument('--udp-spec',  type=str, default=DEFAULT_UDP_RDL_SPEC,
                        help=f'regblock UDPs RDL spec, default {DEFAULT_UDP_RDL_SPEC}')
    parser.add_argument('--dac-spec',  type=str, default=DEFAULT_DAC_RDL_SPEC,
                        help=f'DAC RDL spec, default {DEFAULT_DAC_RDL_SPEC}')
    parser.add_argument('--adc-spec',  type=str, default=DEFAULT_ADC_RDL_SPEC,
                        help=f'ADC RDL spec, default {DEFAULT_ADC_RDL_SPEC}')
    parser.add_argument('--top-spec',  type=str, default=DEFAULT_TOP_RDL_SPEC,
                        help=f'Top-level RDL spec, default {DEFAULT_TOP_RDL_SPEC}')

    parser.add_argument('--top-html',  type=str, default=DEFAULT_TOP_HTML_PATH,
                        help=f'HTML output dir (top-level only), default {DEFAULT_TOP_HTML_PATH}')

    parser.add_argument('--uvmpkg',    type=str, default=DEFAULT_UVM_PKG_PATH,
                        help=f'UVM register package path, default {DEFAULT_UVM_PKG_PATH}')

    parser.add_argument('--dac-rtl',   type=str, default=DEFAULT_DAC_RTL_PATH,
                        help=f'DAC RTL output dir, default {DEFAULT_DAC_RTL_PATH}')
    parser.add_argument('--adc-rtl',   type=str, default=DEFAULT_ADC_RTL_PATH,
                        help=f'ADC RTL output dir, default {DEFAULT_ADC_RTL_PATH}')

    parser.add_argument('--sync',      type=str, default=DEFAULT_REG_SYNC_PATH,
                        help=f'ADC synchronizer output file, default {DEFAULT_REG_SYNC_PATH}')
    
    parser.add_argument('--cheader',    type=str, default=DEFAULT_CHEADER_PATH,
                        help=f'C header output file, default {DEFAULT_CHEADER_PATH}')

    return parser.parse_args()


# ---------------------------------------------------------------------------
# RDL compilation
# ---------------------------------------------------------------------------

def compile_rdl(udp_spec, *paths):
    '''
    Function: compile_rdl

    Compile one or more RDL files into an elaborated root node.

    regblock_udps.rdl is always compiled first so that UDP property
    definitions (e.g. `activehigh`, `activelow`, `intr`, `nonsticky`) are
    in scope when the register specs are parsed. The ALL_UDPS list registers
    the corresponding Python-side UDP handlers with the compiler so that
    peakrdl-regblock knows how to generate RTL for each one.

    Parameters:
        udp_spec - path to regblock_udps.rdl (compiled before all others)
        *paths   - one or more RDL source file paths, compiled in order

    Returns:
        Elaborated RDL root node
    '''
    rdlc = RDLCompiler()

    for udp in ALL_UDPS:
        rdlc.register_udp(udp)

    try:
        rdlc.compile_file(udp_spec)
        for path in paths:
            rdlc.compile_file(path)
        root = rdlc.elaborate()
    except RDLCompileError:
        sys.exit(1)

    return root


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def gen_uvm_pkg(root, filename, **kwargs):
    '''
    Function: gen_uvm_pkg

    Generate a UVM register package from the given elaborated root.

    Parameters:
        root     - elaborated RDL root node
        filename - output .sv file path
    '''
    exporter = UVMExporter(**kwargs)
    exporter.export(root, filename, use_uvm_factory=True)


def gen_html(root, path, **kwargs):
    '''
    Function: gen_html

    Generate HTML register documentation.

    Parameters:
        root - elaborated RDL root node
        path - output directory path
    '''
    exporter = HTMLExporter(**kwargs)
    exporter.export(root, path, home_url='../')


def gen_dac_rtl(root, path, **kwargs):
    '''
    Function: gen_dac_rtl

    Generate SystemVerilog RTL for the DAC register block using an AXI4-Lite
    CPUIF. The DAC lives on the Zynq PL fabric and is accessed directly over
    AXI from the PS.

    Parameters:
        root - elaborated RDL root node (dac_regs)
        path - output directory path
    '''
    exporter = RegblockExporter(**kwargs)
    exporter.export(
        root, path,
        cpuif_cls=AXI4Lite_Cpuif,
        generate_hwif_report=True,
        module_name='dac_regs_mod',
        retime_read_response=True,
    )


def gen_adc_rtl(root, path, **kwargs):
    '''
    Function: gen_adc_rtl

    Generate SystemVerilog RTL for the ADC register block using a passthrough
    CPUIF. The passthrough signals are wired to an external SPI master that
    communicates with the off-fabric device housing the ADC registers and
    conversion memory.

    Parameters:
        root - elaborated RDL root node (adc_regs)
        path - output directory path
    '''
    exporter = RegblockExporter(**kwargs)
    exporter.export(
        root, path,
        cpuif_cls=PassthroughCpuif,
        generate_hwif_report=True,
        module_name='adc_regs_mod',
        retime_read_response=True,
    )


def gen_sync(root, filename, **kwargs):
    '''
    Function: gen_sync

    Generate SystemVerilog clock-domain synchronizer RTL for the ADC register
    interface (SPI clock -> system clock).

    Parameters:
        root     - elaborated RDL root node (adc_regs)
        filename - output .sv file path
    '''
    exporter = RTLSyncExporter(**kwargs)
    exporter.export(root, filename)


def gen_cheader(root, filename, **kwargs):
    '''
    Function: gen_cheader

    Generate a C header file containing register offsets and bitfield macros for
    software driver use.

    Parameters:
        root     - elaborated RDL root node (chip_top)
        filename - output .h file path
    '''
    exporter = CHeaderExporter(**kwargs)
    exporter.export(root, filename)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    '''
    Function: main

    Orchestrates all compilation and export steps:

    1. DAC  — compile dac_registers.rdl  -> AXI4-Lite RTL
    2. ADC  — compile adc_registers.rdl  -> passthrough RTL + synchronizer
    3. Top  — compile chip_top.rdl       -> unified UVM RAL package + HTML
    '''
    args = parse_input_arguments()

    # ------------------------------------------------------------------
    # 1. DAC: AXI4-Lite RTL
    # ------------------------------------------------------------------
    print('[registers.py] Compiling DAC registers...')
    dac_root = compile_rdl(args.udp_spec, args.dac_spec)
    gen_dac_rtl(dac_root, args.dac_rtl)

    # ------------------------------------------------------------------
    # 2. ADC: passthrough RTL + synchronizer
    # ------------------------------------------------------------------
    print('[registers.py] Compiling ADC registers...')
    adc_root = compile_rdl(args.udp_spec, args.adc_spec)
    gen_adc_rtl(adc_root, args.adc_rtl)
    gen_sync(adc_root, args.sync)

    # ------------------------------------------------------------------
    # 3. Top: unified UVM RAL + HTML
    #    chip_top.rdl `include`s both sub-maps, so we only need to pass
    #    the top file; the RDL compiler resolves the includes itself.
    #    The UDPs file must still be compiled first in a fresh RDLCompiler
    #    instance — `include` does not pull in the Python UDP registrations.
    # ------------------------------------------------------------------
    print('[registers.py] Compiling chip_top for UVM RAL...')
    top_root = compile_rdl(args.udp_spec, args.top_spec)
    gen_uvm_pkg(top_root, args.uvmpkg,
                user_template_dir='./scripts/peakrdl_templates')
    gen_html(top_root, args.top_html)
    gen_cheader(top_root, args.cheader)

    print('[registers.py] Done.')


if __name__ == '__main__':
    main()
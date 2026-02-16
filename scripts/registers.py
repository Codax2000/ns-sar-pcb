'''
Script: gen_registers.py

Generates the following for the ADC registers:

- HTML description page
- UVM register package
- SystemVerilog RTL using <OBI: https://github.com/openhwgroup/obi> as a
  register interface
- A synchronizer that goes from the SPI clock to the system clock, if necessary
'''


import sys
import argparse
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl_uvm import UVMExporter
from peakrdl_html import HTMLExporter
from peakrdl_regblock import RegblockExporter
from peakrdl_regblock.cpuif.obi import OBI_Cpuif
from peakrdl_regblock.udps import ALL_UDPS
from synchronizer_exporter import RTLSyncExporter


# Variable: DEFAULT_RDL_SPEC
# Defines the default path to the RDL register spec file
DEFAULT_RDL_SPEC = './hdl_design/hdl_design.srcs/registers/registers.rdl'

# Variable: DEFAULT_HTML_PATH
# Defines the default path to the directory in which the HTML documentation
# will be stored
DEFAULT_HTML_PATH = './adc_regs'

# Variable: DEFAULT_UVM_PKG_PATH
# Defines the default path to the file which will contain UVM registers
DEFAULT_UVM_PKG_PATH = \
    './hdl_design/hdl_design.srcs/dv/reg_env/adc_regs_pkg.svh'

# Variable: DEFAULT_REG_RTL_PATH
# Path to the directory in which the RTL package and path will be stored
DEFAULT_REG_RTL_PATH = './hdl_design/hdl_design.srcs/rtl/registers'

# Variable: DEFAULT_REG_SYNC_PATH
# Path to the file in which the ADC register synchronizer will be stored,
# if it's used
DEFAULT_REG_SYNC_PATH = \
    './hdl_design/hdl_design.srcs/rtl/registers/adc_reg_sync.sv'


'''
Function: parse_input_arguments

Parse the given keyword arguments using argparse. Use

--- Code
python registers.py --help
---

for more information about keyword args.
'''
def parse_input_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--spec', type=str, default=DEFAULT_RDL_SPEC,
                        help=f"RDL Spec path, default {DEFAULT_RDL_SPEC}")
    parser.add_argument('--html', type=str, default=DEFAULT_HTML_PATH,
                        help=f"Output HTML directory, default {
                            DEFAULT_HTML_PATH}")
    parser.add_argument('--uvmpkg', type=str, default=DEFAULT_UVM_PKG_PATH,
                        help=f'Output UVM register package path, default {
                            DEFAULT_UVM_PKG_PATH}')
    parser.add_argument('--rtl', type=str, default=DEFAULT_REG_RTL_PATH,
                        help=f'Output register RTL path, default {
                            DEFAULT_REG_RTL_PATH}')
    parser.add_argument('--sync', type=str, default=DEFAULT_REG_SYNC_PATH,
                        help=f'Output synchronizer path, default {
                            DEFAULT_REG_SYNC_PATH}')

    return parser.parse_args()


'''
Function: compile_rdl

Compile the RDL from the given RDL spec file and return the RDL Compiler object
that can be used for export.

Parameters:
    path - relative path from invocation to the RDL spec file

Returns:
    The elaborated RDL Compiler
'''
def compile_rdl(path):
    rdlc = RDLCompiler()

    for udp in ALL_UDPS:
        rdlc.register_udp(udp)

    try:
        rdlc.compile_file(path)
        root = rdlc.elaborate()
    except RDLCompileError:
        sys.exit(1)

    return root


'''
Function: gen_uvm_pkg

Generate UVM register model for the given RDL.

Parameters:
    root - the RDL compiler elaborated object used for export
    filename - the path to the desired file
'''
def gen_uvm_pkg(root, filename, **kwargs):
    exporter = UVMExporter(**kwargs)
    exporter.export(root, filename)


'''
Function: gen_html

Generate HTML documentation for the given RDL.

Parameters:
    root - the RDL compiler elaborated object used for export
    filename - the path to the desired HTML directory
'''
def gen_html(root, filename, **kwargs):
    exporter = HTMLExporter(**kwargs)
    exporter.export(root, filename)


'''
Function: gen_rtl

Generate SystemVerilog RTL for the given RTL

Parameters:
    root - the RDL compiler elaborated object used for export
    filename - the path to the desired RTL directory
'''
def gen_rtl(root, filename, **kwargs):
    exporter = RegblockExporter(**kwargs)
    exporter.export(root, filename, cpuif_cls=OBI_Cpuif,
                    default_reset_activelow=True, generate_hwif_report=True)


'''
Function: gen_sync

Generate SystemVerilog RTL for synchronizers to the interface clock

Parameters:
    root - the RDL compiler elaborated object used for export
    filename - the path to the desired RTL directory. Must end in .sv
'''
def gen_sync(root, filename, **kwargs):
    exporter = RTLSyncExporter(**kwargs)
    exporter.export(root, filename)


'''
Function: main

Runs RDL compiler and generates register export files.
'''
def main():
    args = parse_input_arguments()
    root = compile_rdl(args.spec)
    gen_uvm_pkg(root, args.uvmpkg)
    gen_html(root, args.html)
    gen_rtl(root, args.rtl)
    gen_sync(root, args.sync)


if __name__ == '__main__':
    main()

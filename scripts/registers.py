import sys
import argparse
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl_uvm import UVMExporter
from peakrdl_html import HTMLExporter
from peakrdl_regblock import RegblockExporter
from peakrdl_regblock.cpuif.axi4lite import AXI4Lite_Cpuif
from peakrdl_regblock.udps import ALL_UDPS


DEFAULT_RDL_SPEC = './hdl_design/hdl_design.srcs/registers/registers.rdl'
DEFAULT_HTML_PATH = './adc_regs'
DEFAULT_UVM_PKG_PATH = './hdl_design/hdl_design.srcs/dv/reg_env/adc_regs_pkg.svh'
DEFAULT_REG_RTL_PATH = './hdl_design/hdl_design.srcs/rtl/registers'
DEFAULT_REG_SYNC_PATH = './hdl_design/hdl_design.srcs/rtl/registers/adc_reg_sync.sv'


def parse_input_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--spec', type=str, default=DEFAULT_RDL_SPEC,
                        help="RDL Spec path")
    parser.add_argument('--html', type=str, default=DEFAULT_HTML_PATH,
                        help="Output HTML Argument")
    parser.add_argument('--uvmpkg', type=str, default=DEFAULT_UVM_PKG_PATH,
                        help='Output UVM register package path')
    parser.add_argument('--rtl', type=str, default=DEFAULT_REG_RTL_PATH,
                        help='Output register RTL path')
    parser.add_argument('--sync', type=str, default=DEFAULT_REG_SYNC_PATH,
                        help='Output synchronizer path')
    
    return parser.parse_args()


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


def gen_uvm_pkg(root, filename, **kwargs):
    exporter = UVMExporter(**kwargs)
    exporter.export(root, filename)


def gen_html(root, filename, **kwargs):
    exporter = HTMLExporter(**kwargs)
    exporter.export(root, filename)


def gen_rtl(root, filename, **kwargs):
    exporter = RegblockExporter(**kwargs)
    exporter.export(root, filename, cpuif_cls=AXI4Lite_Cpuif)


def main():
    args = parse_input_arguments()
    root = compile_rdl(args.spec)
    gen_uvm_pkg(root, args.uvmpkg)
    gen_html(root, args.html)
    gen_rtl(root, args.rtl)


if __name__ == '__main__':
    main()
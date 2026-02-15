import sys
from systemrdl import RDLCompiler, RDLCompileError
from peakrdl_uvm import UVMExporter
from peakrdl_html import HTMLExporter


def compile_rdl(path):
    rdlc = RDLCompiler()

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


def main():
    input_rdl = './registers.rdl'
    root = compile_rdl(input_rdl)
    gen_uvm_pkg(root, './adc_regs.svh')
    gen_html(root, './adc_regs')
    

if __name__ == '__main__':
    main()
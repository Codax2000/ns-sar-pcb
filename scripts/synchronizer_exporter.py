import sys
import pdb

from systemrdl import RDLCompiler, RDLCompileError
from systemrdl.walker import RDLSimpleWalker
from systemrdl.walker import RDLListener
from systemrdl.node import FieldNode

# Define a listener that will print out the register model hierarchy
class MyModelPrintingListener(RDLListener):

    def enter_Field(self, node):
        # Print some stuff about the field
        sw_access_str = f"hw={node.get_property('hw').name}"
        hwif_path = node.get_path().split('.')[1:]
        hwif_path = '.'.join(hwif_path)
        if node.get_property('hw').name == 'r':
            hwif_name = 'hwif_in'
            hwif_value = 'next'
        else:
            hwif_name = 'hwif_out'
            hwif_value = 'value'
        hwif_path = f'{hwif_name}.{hwif_path}.{hwif_value}'

        # unnecessary with synchronizer
        # if node.width > 1:
        #     hwif_path = f'{hwif_path}[{node.width - 1}:0]'

        print(sw_access_str, hwif_path)

rdlc = RDLCompiler()
try:
    # Compile all the files provided
    rdlc.compile_file('./hdl_design/hdl_design.srcs/registers/registers.rdl')

    # Elaborate the design
    root = rdlc.elaborate()
except RDLCompileError:
    # A compilation error occurred. Exit with error code
    sys.exit(1)

walker = RDLSimpleWalker(unroll=True)
listener = MyModelPrintingListener()
walker.walk(root, listener)
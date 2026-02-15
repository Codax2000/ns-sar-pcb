import sys
import pdb

from systemrdl import RDLCompiler, RDLCompileError
from systemrdl.walker import RDLSimpleWalker
from systemrdl.walker import RDLListener
from systemrdl.node import FieldNode

# Define a listener that will print out the register model hierarchy
class MyModelPrintingListener(RDLListener):

    def enter_Addrmap(self, node):
        name = node.inst_name

        n_sync_stages = 2
        print(f'module #(')
        print(f'\tparameter N_SYNC_STAGES={n_sync_stages},')
        print(f'\tparameter SRC_INPUT_REG={0}')
        print(f') {name}_reg_sync (')
        print(f'\t{name}__in_t hwif_in_sysclk')
        print(f'\t{name}__in_t hwif_in_ifclk')
        print(f'\t{name}__out_t hwif_out_sysclk')
        print(f'\t{name}__out_t hwif_out_ifclk')
        print('\tinput logic sysclk,')
        print('\tinput logic ifclk\n);')

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
        hwif_in_path = f'\t{hwif_name}.{hwif_path}.{hwif_value}'
        hwif_out_path = f'\t{hwif_name}.{hwif_path}.{hwif_value}'

        # unnecessary with synchronizer
        # if node.width > 1:
        #     hwif_path = f'{hwif_path}[{node.width - 1}:0]'
        print('sync_nstage #(')
        print('\t.N_SYNC_STAGES(N_SYNC_STAGES),')
        print('\t.SRC_INPUT_REG(SRC_INPUT_REG),')
        print(f"\t.N_BITS({node.width})")
        print(f") {'.'.join(hwif_path.split('.')[1:3]).replace('.', '_')}_sync (")
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
'''
Script: synchronizer_exporter

PeakRDL-compliant exporter for generating CDC synchronizers for generated
hardware interfaces from the interface clock and back again. Contains
the <RTLSyncExporter> class, which runs the export itself, and the
<RTLSyncExporterPlugin> class, which should run with the PeakRDL command-line
tool.
'''
from typing import TYPE_CHECKING
from peakrdl.plugins.exporter import ExporterSubcommandPlugin
from systemrdl.node import Node, AddrmapNode
from systemrdl.walker import RDLSimpleWalker
from systemrdl.walker import RDLListener
if TYPE_CHECKING:
    import argparse

import pdb


'''
Class: RTLSyncExporter

For each field in the hardware interface, generates a CDC synchronizer that
goes ifclk -> sysclk if the field is hardware-readable, and sysclk -> ifclk if
the field is hardware-writeable. These two should be mutually exclusive.
'''
class RTLSyncExporter:

    '''
    Class: _SyncFieldListener

    Listener for a traversal of the top node that will generate a file at the
    initializer path when walked.
    '''
    class _SyncFieldListener(RDLListener):

        '''
        Function: __init__

        Parameters:
            path - the relative path at which the listener will create the
            output RTL.
        '''
        def __init__(self, path: str):
            super().__init__()

            last_path = path.split('.')[-1]
            if (last_path != 'sv'):
                raise ValueError('Path must point to a file ending in .sv')
            self.path = path

        '''
        Function: enter_Addrmap

        Defines what to do when an Addrmap node is first encountered. In this
        case, declares the {addrmap_name}_reg_sync module declaration.
        '''
        def enter_Addrmap(self, node):
            self.f = open(self.path, 'w')
            name = node.inst_name

            n_sync_stages = 2
            print(f'// Module: {name}_reg_sync', file=self.f)
            print('// Instantiates CDC synchronizers for the CSR registers.',
                  file=self.f)
            print(
                '// Automatically generated from registers.rdl using PeakRDL.',
                file=self.f)
            print(f'import {name}_mod_pkg::*;', file=self.f)
            print(f'module {name}_reg_sync #(', file=self.f)
            print(f'\tparameter N_SYNC_STAGES={n_sync_stages},', file=self.f)
            print(f'\tparameter SRC_INPUT_REG={0}', file=self.f)
            print(') (', file=self.f)
            print(f'\tinput {name}__in_t hwif_in_sysclk,', file=self.f)
            print(f'\tinput {name}__in_t hwif_in_ifclk,', file=self.f)
            print(f'\toutput {name}__out_t hwif_out_sysclk,', file=self.f)
            print(f'\toutput {name}__out_t hwif_out_ifclk,', file=self.f)
            print('\tinput logic sysclk,', file=self.f)
            print('\tinput logic ifclk,', file=self.f)
            print('\tinput logic sysclk_rst,', file=self.f)
            print('\tinput logic ifclk_rst\n);\n', file=self.f)

        '''
        Function: enter_Field

        Defines what to do when a Field node is first encountered. In this
        case, instantiates an instance of <sync_nstage> for that field. If the
        field is hw=r, then the synchronizer goes ifclk -> sysclk, otherwise
        sysclk -> ifclk.
        '''
        def enter_Field(self, node):
            # Print some stuff about the field
            hwif_path = node.get_path().split('.')[1:]
            hwif_path = '.'.join(hwif_path)
            if node.get_property('hw').name == 'r':
                hwif_name = 'hwif_out'
                hwif_value = 'value'
                hwif_srcclk = 'ifclk'
                hwif_destclk = 'sysclk'
            else:
                hwif_name = 'hwif_in'
                hwif_value = 'next'
                hwif_destclk = 'ifclk'
                hwif_srcclk = 'sysclk'

            self.print_sync_declaration(hwif_name, hwif_value, hwif_srcclk,
                                        hwif_destclk, hwif_path, node)
        
        '''
        Function: print_sync_declaration

        Utility function to shorten how hard it is to print the synchronizer
        declaration. Takes in several things about the field and prints it
        to self.f.
        '''
        def print_sync_declaration(self, hwif_name, hwif_value, hwif_srcclk,
                                   hwif_destclk, hwif_path, node):
            
            hwif_in_path = f'{hwif_name}_{hwif_srcclk}.{
                hwif_path}.{hwif_value}'
            hwif_out_path = f'{hwif_name}_{hwif_destclk}.{
                hwif_path}.{hwif_value}'

            print('\tsync_nstage #(', file=self.f)
            print('\t\t.N_SYNC_STAGES(N_SYNC_STAGES),', file=self.f)
            print('\t\t.SRC_INPUT_REG(SRC_INPUT_REG),', file=self.f)
            print(f"\t\t.N_BITS({node.width})", file=self.f)
            print(f"\t) sync_{'.'.join(hwif_path.split('.')[:3]).replace('.', '_')} (", file=self.f)
            print(f'\t\t.src_clk({hwif_srcclk}),', file=self.f)
            print(f'\t\t.dest_clk({hwif_destclk}),', file=self.f)
            print(f'\t\t.src_data({hwif_in_path}),', file=self.f)
            print(f'\t\t.dest_data({hwif_out_path}),', file=self.f)
            print(f'\t\t.dest_clk_rst({hwif_destclk}_rst)', file=self.f)
            print('\t);\n', file=self.f)

        '''
        Function: exit_Addrmap

        Defines the last thing to do when an Addrmap node is encountered. In
        this case, terminates the module and closes the RTL file.
        '''
        def exit_Addrmap(self, node):
            print(f'endmodule : {node.inst_name}_reg_sync', file=self.f)
            self.f.close()

    '''
    Function: export

    Export the fields in the given node to the given synchronizer file.

    Parameters:
        node - toplevel Root or Addrmap node.
        path - relative string path to the synchronizer file. Must end in ".sv"
    '''
    def export(self, node: Node, path: str, **kwargs):
        walker = RDLSimpleWalker(unroll=True)
        listener = self._SyncFieldListener(path)
        walker.walk(node, listener)


'''
Class: RTLSyncExporterPlugin

PeakRDL-compliant (hopefully) wrapper around the RTLSyncExporter. Should be
usable with the PeakRDL CLI.
'''
class RTLSyncExporterPlugin(ExporterSubcommandPlugin):
    short_desc = 'Plugin for the RTL Synchronizer exporter'
    long_desc = 'Generates synthesizeable RTL for synchronizing registers to system clock and interface clock'

    '''
    Function: add_exporter_arguments

    Adds the --path argument to the command-line arguments. Defaults to ./cdc_sync.sv.
    '''
    def add_exporter_arguments(self, arg_group: 'argparse.ArgumentParser') -> None:
        arg_group.add_argument('--path', type=str, default='./cdc_sync.sv',
                               help='Path to generated synchronizer RTL, default ./cdc_sync.sv. Must end in .sv.')

    '''
    Function: do_export

    Exports the given top node with the given command-line options.
    '''
    def do_export(self, top_node: 'AddrmapNode', options: 'argparse.Namespace') -> None:
        exporter = RTLSyncExporter()
        exporter.export(top_node, options.path)

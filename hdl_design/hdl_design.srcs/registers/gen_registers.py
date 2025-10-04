'''
Generates all necessary files for register mapping. Should be fully portable
across projects. Implements utility functions and generates register CSV values
for readability. Address space is defined as a global parameter

Generated files:
- ral_dut_cfg.sv : UVM RAL support, building out the register objects and the register map,
                   including internal memories.
- fields.csv     : CSV of fields, sizes, descriptions, etc, in the same order as in fields.json
- reg_map.csv    : CSV of register map, not including memories
- registers.sv   : Generated register RTL
'''


import json
import os
import pandas as pd
import pdb


FIELDS_PATH = './hdl_design/hdl_design.srcs/registers/fields.json'
REG_IF_PATH = './hdl_design/hdl_design.srcs/registers/fields.csv'
REGISTERS_PATH = 
RAL_DUT_CONFIG_PATH
FIELD_WIDTH = 16


def gen_fields_sheet(data, save_csv=True):
    '''
    Reads in the given JSON object and generates fields.csv in the same
    directory, if the option is enabled. Then, returns the generated DataFrame.

    Arguments:
        data     : object : JSON fields data
        save_csv : bool   : if true, save to a file called "fields.csv"
    
    Return:
        DataFrame : register fields as entries in a database
    '''
    df = pd.DataFrame.from_dict(data, orient='index')
        
    df['lsb_bit_position'] = df['lsb_bit_position'].fillna(0).astype(int)
    df['reset_value'] = df['reset_value'].fillna(0).astype(int)
    df['volatile'] = df['volatile'].fillna(0).astype(int)
    
    df = df.reset_index(names='field_name')

    if save_csv:
        df.to_csv('./hdl_design/hdl_design.srcs/registers/fields.csv', index=False)
    
    return df


def gen_field_map(data):
    '''
    Using the given DataFrame, generates a field map CSV for the given register
    fields and saves it as reg_map.csv.

    Arguments:
        data : DataFrame : register fields
    '''
    top_address = data['reg_address'].max()
    with open('./hdl_design/hdl_design.srcs/registers/reg_map.csv', 'w') as f:
        # print headers in CSV
        print('address', file=f, end='')
        for i in range(15,-1,-1):
            print(f',{i}', file=f, end='')
        print(file=f)

        # print register mapping
        for addr in range(0, top_address + 1):

            register_fields = data.loc[data['reg_address'] == addr, 
                                       ['field_name', 'width',
                                        'lsb_bit_position']]
            print(f'{addr}', file=f, end='')
            register_fields = register_fields.sort_values(by='lsb_bit_position')
            reg_string = ''

            # use a while loop to allow incrementing of the loop counter
            i = 0
            while i < FIELD_WIDTH:
                filt = register_fields['lsb_bit_position'] == i
                if len(register_fields[filt]) > 0:
                    reg_name = register_fields.loc[filt, 'field_name'].iloc[0]
                    reg_width = register_fields.loc[filt, 'width'].iloc[0]
                    for j in range(reg_width):
                        reg_string = f',{reg_name}[{j}]{reg_string}'

                        # if the length of the register is more than 0,
                        # increment the loop counter to account for multiple
                        # cells being filled
                        if (j > 0):
                            i += 1
                else:
                    reg_string = f',reserved{reg_string}'
                i += 1
            print(reg_string, file=f)


def get_fields_at_register_address(data, reg_addr):
    '''
    Returns the fields in the given DataFrame at the given reg_addr as a list
    of strings

    Arguments:
        data     : DataFrame : register fields DataFrame
        reg_addr : int       : register address for which to get the fields
    
    Return:
        list : list of register field names at the given address
    '''
    filt = data['reg_address'] == reg_addr
    fields = list(data.loc[filt, 'field_name'])
    return fields


def parse_registers_json(path):
    '''
    Given a path to the registers JSON file, reads it and returns a Python
    object matching it.

    Arguments:
        path : string : path to the registers JSON file
    '''
    with open(path) as f:
        fields = json.load(f)

    return fields


def add_register_object_to_ral(fields, address, file):
    '''
    Given a fields DataFrame and an address, print the necessary register
    to a uvm_reg object in the given file.

    Arguments:
        fields  : DataFrame : register field DataFrame
        address : int       : register address to define
        file    : file      : text file to which to print field definition
    '''
    print(f'class ral_register_{address} extends uvm_reg;', file=file)
    for reg_field in get_fields_at_register_address(fields, address):
        print(f'    uvm_reg_field {reg_field};', file=file)
    print(file=file)
    print(f'    `uvm_reg_utils(ral_register_{address})', file=file, end='\n\n')
    print(f'    function new (string name = "ral_register_{address}");', file=file)

    # TODO: check back over the coverage of this, not sure how coverage should go
    print(f'        super.new(name,{FIELD_WIDTH},build_coverage(UVM_NO_COVERAGE))', 
          file=file)
    print(f'    endfunction', file=file, end='\n\n')

    print('    virtual function void build();', file=file)
    for reg_field in get_fields_at_register_address(fields, address):
        print(f'        this.{reg_field} = uvm_reg_field::type_id::create("{reg_field}", , get_full_name());', file=file)
        field_row = fields[fields['field_name'] == reg_field]
        print(f'        this.{reg_field}.configure(', file=file)
        print(f'            this,', file=file)
        # print(f'            {field_row['width'].iloc[0]},', file=file)
        # print(f'            {field_row['lsb_bit_position'].iloc[0]},', file=file)
        # print(f'            {field_row['access'].iloc[0]},', file=file)
        # print(f'            {field_row['volatile'].iloc[0]},', file=file)
        # print(f'            {field_row['reset_value'].iloc[0]},', file=file)
        print(f'            1,', file=file)
        print(f'            0,', file=file)
        print(f'            0', file=file)
        print(f'        );', file=file)
    print('    endfunction', file=file, end='\n\n')
    print('endclass', file=file, end='\n\n')


def generate_ral_config_file(fields):
    '''
    Generate the ral_dut_cfg.sv file contents.

    Arguments:
        fields : DataFrame : register fields with information
    '''
    with open('./hdl_design/hdl_design.srcs/dv/env/ral_dut_cfg.sv', 'w') as file:
        print('import uvm_pkg::*;', file=file)
        print('`include "uvm_macros.svh"`', file=file, end='\n\n')
        for idx in fields['reg_address'].unique():
            add_register_object_to_ral(fields, idx, file)
        
        print('class dut_registers extends uvm_reg_block;', file=file)
        for idx in fields['reg_address'].unique():
            print(f'    ral_register_{idx} register_{idx};', file=file)
        print(file=file)

        print('    `uvm_object_utils(dut_registers)', file=file, end='\n\n')

        print('    function new (string name = "dut_registers");', file=file)
        print('        super.new(name, build_coverage(UVM_NO_COVERAGE));', file=file)
        print('    endfunction', file=file, end='\n\n')

        print('    virtual function build();', file=file)
        print('        this.default_map = create_map("default_map", 0, 2, UVM_LITTLE_ENDIAN);',
              file=file, end='\n\n')
        for idx in fields['reg_address'].unique():
            print(f'        this.register_{idx} = ral_register_{idx}::type_id::create("register_{idx}", , get_full_name());', file=file)
            print(f'        this.register_{idx}.configure(this, null, "");', file=file)
            print(f'        this.register_{idx}.build();', file=file)
            print(f'        this.default_map.add_reg(this.register_{idx}, `UVM_REG_ADDR_WIDTH\'h{idx}, "RW")', file=file, end='\n\n')
        
        print('    endfunction', file=file)
        print('endclass', file=file)


def generate_interface_file(fields):
    '''
    Generates the interface.sv file for use in passing registers around the
    design. Generates it in the rtl/registers directory

    Arguments:
        fields : DataFrame : register field dataframe with access type
    '''
    with open(REG_IF_PATH, 'w') as file:
        print('interface reg_if;', file=file)
        for field in fields['field_name']:
            width = fields.loc[fields['field_name'] == field, 'width'].iloc[0]
            if width == 1:
                print(f'    logic {field};', file=file)
            else:
                print(f'    logic [{width-1}:0] {field};', file=file)
        
        print('', file=file)
        is_writeable = (fields['access'] == 'W1C') | (fields['access'] == 'RW')
        print('    modport WR_BUS_IF (', file=file)
        for field in fields[is_writeable]['field_name']:
            print(f'        output {field};', file=file)
        for field in fields[~is_writeable]['field_name']:
            print(f'        input {field};', file=file)
        print('    );', file=file, end='\n\n')

        print('    modport RD (', file=file)
        for field in fields['field_name']:
            print(f'        input {field};', file=file)
        print('    );', file=file, end='\n\n')
        
        print('    modport WR_RO (', file=file)
        for field in fields[~is_writeable]['field_name']:
            print(f'        output {field};', file=file)
        for field in fields[is_writeable]['field_name']:
            print(f'        input {field};', file=file)
        print('    );', file=file, end='\n\n')

        for field in fields[~is_writeable]['field_name']:
            print(f'    modport WR_{field} (output {field});', file=file)

        print('\nendinterface', file=file)


def remove_generated_files():
    '''
    Removes all generated files before regeneration
    '''
    if os.path.isfile(REG_IF_PATH):
        os.remove(REG_IF_PATH)
    if os.path.isfile('./hdl_design/hdl_design.srcs/dv/env/ral_dut_cfg.sv'):
        os.remove('./hdl_design/hdl_design.srcs/dv/env/ral_dut_cfg.sv')
    if os.path.isfile('./hdl_design/hdl_design.srcs/registers/reg_map.csv'):
        os.remove('./hdl_design/hdl_design.srcs/registers/reg_map.csv')
    if os.path.isfile('./hdl_design/hdl_design.srcs/registers/fields.csv'):
        os.remove('./hdl_design/hdl_design.srcs/registers/fields.csv')


def main():
    remove_generated_files()
    fields_json = parse_registers_json(FIELDS_PATH)
    fields_df = gen_fields_sheet(fields_json)
    gen_field_map(fields_df)
    generate_ral_config_file(fields_df)
    generate_interface_file(fields_df)


if __name__ == '__main__':
    main()
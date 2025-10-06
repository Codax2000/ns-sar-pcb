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


import pandas as pd
import json
import os
import pdb


FIELDS_PATH = './hdl_design/hdl_design.srcs/registers/fields.json'
MEMORIES_PATH = './hdl_design/hdl_design.srcs/registers/memories.json'

REGISTERS_RTL_PATH = './hdl_design/hdl_design.srcs/rtl/registers/registers.sv'
MEMORIES_RTL_PATH = './hdl_design/hdl_design.srcs/rtl/registers/memories.sv'
REG_IF_PATH = './hdl_design/hdl_design.srcs/rtl/registers/reg_if.sv'

RAL_DUT_CONFIG_PATH = './hdl_design/hdl_design.srcs/dv/env/ral_dut_cfg.sv'

REG_MAP_CSV_PATH = './hdl_design/hdl_design.srcs/registers/reg_map.csv'
FIELDS_CSV_PATH = './hdl_design/hdl_design.srcs/registers/fields.csv'
MEMORIES_CSV_PATH = './hdl_design/hdl_design.srcs/registers/memories.csv'

FIELD_WIDTH = 16
ADDR_WIDTH  = 14  # for this device, register addresses are 2^14-1, above that is memory


def gen_fields_sheet(data, save_csv=True):
    '''
    Reads in the given JSON object and generates fields.csv in the same
    directory, if the option is enabled. Then, returns the generated DataFrame.

    Arguments:
        data     : object : JSON fields data
        save_csv : bool   : if true, save to a file called "fields.csv".
                            Default True.

    Return:
        DataFrame : register fields as entries in a database
    '''
    df = pd.DataFrame.from_dict(data, orient='index')

    df['lsb_bit_position'] = df['lsb_bit_position'].fillna(0).astype(int)
    df['reset_value'] = df['reset_value'].fillna(0).astype(int)
    df['volatile'] = df['volatile'].fillna(0).astype(int)

    df = df.reset_index(names='field_name')

    if save_csv:
        df.to_csv(FIELDS_CSV_PATH, index=False)

    return df


def gen_memories_sheet(path, save_csv=False):
    '''
    Reads in the given json path and returns the table as a DataFrame.
    If save_csv is True, saves to a CSV

    Arguments:
        data     : string : memory JSON file path
        save_csv : bool   : if true, save to a file called "memories.csv".
                            Default False.

    Return:
        DataFrame : memories as entries in a database
    '''
    df = pd.read_json(path, orient='index')
    df = df.reset_index(names='mem_name')

    if save_csv:
        df.to_csv(MEMORIES_CSV_PATH, index=False)
    return df


def gen_field_map(data):
    '''
    Using the given DataFrame, generates a field map CSV for the given register
    fields and saves it as reg_map.csv.

    Arguments:
        data : DataFrame : register fields
    '''
    top_address = data['reg_address'].max()
    with open(REG_MAP_CSV_PATH, 'w') as f:
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
    print(f'    `uvm_object_utils(ral_register_{address})', file=file, end='\n\n')
    print(f'    function new (string name = "ral_register_{address}");', file=file)

    # TODO: check back over the coverage of this, not sure how coverage should go
    print(f'        super.new(name,{FIELD_WIDTH},build_coverage(UVM_NO_COVERAGE));',
          file=file)
    print(f'    endfunction', file=file, end='\n\n')

    print('    virtual function void build();', file=file)
    for reg_field in get_fields_at_register_address(fields, address):
        print(f'        this.{reg_field} = uvm_reg_field::type_id::create("{reg_field}", , get_full_name());', file=file)
        field_row = fields[fields['field_name'] == reg_field]
        print(f'        this.{reg_field}.configure(', file=file)
        print(f'            this,', file=file)
        print(f'            {field_row['width'].iloc[0]},', file=file)
        print(f'            {field_row['lsb_bit_position'].iloc[0]},', file=file)
        print(f'            "{field_row['access'].iloc[0]}",', file=file)
        print(f'            {field_row['volatile'].iloc[0]},', file=file)
        print(f'            {field_row['reset_value'].iloc[0]},', file=file)
        print(f'            1,', file=file)
        print(f'            0,', file=file)
        print(f'            0', file=file)
        print(f'        );', file=file)
    print('    endfunction', file=file, end='\n\n')
    print('endclass', file=file, end='\n\n')


def generate_ral_config_file(fields, memories):
    '''
    Generate the ral_dut_cfg.sv file contents.

    Arguments:
        fields   : DataFrame : register fields with information
        memories : DataFrame : memories with relevant information
    '''
    with open(RAL_DUT_CONFIG_PATH, 'w') as file:
        print('import uvm_pkg::*;', file=file)
        print('`include "uvm_macros.svh"', file=file, end='\n\n')
        for idx in fields['reg_address'].unique():
            add_register_object_to_ral(fields, idx, file)

        print('class dut_memory extends uvm_reg_block;', file=file)
        for idx in fields['reg_address'].unique():
            print(f'    ral_register_{idx} register_{idx};', file=file)
        for mem_name in memories['mem_name'].unique():
            print(f'    uvm_mem {mem_name.lower()};', file=file)

        print(file=file)

        print('    `uvm_object_utils(dut_memory)', file=file, end='\n\n')

        print('    function new (string name = "dut_memory");', file=file)
        print('        super.new(name, build_coverage(UVM_NO_COVERAGE));', file=file)
        print('    endfunction', file=file, end='\n\n')

        print('    virtual function build();', file=file)
        print('        this.default_map = create_map("default_map", 0, 2, UVM_LITTLE_ENDIAN);',
              file=file, end='\n\n')
        for idx in fields['reg_address'].unique():
            print(f'        this.register_{idx} = ral_register_{idx}::type_id::create("register_{idx}", , get_full_name());', file=file)
            print(f'        this.register_{idx}.configure(this, null, "");', file=file)
            print(f'        this.register_{idx}.build();', file=file)
            print(f'        this.default_map.add_reg(this.register_{idx}, `UVM_REG_ADDR_WIDTH\'h{idx}, "RW");', file=file, end='\n\n')
        for mem_name in memories['mem_name'].unique():
            # pdb.set_trace()
            access = memories.loc[memories['mem_name'] == mem_name, 'access'].iloc[0]
            data_width = memories.loc[memories['mem_name'] == mem_name, 'data_width'].iloc[0]
            addr_width = memories.loc[memories['mem_name'] == mem_name, 'n_address_bits'].iloc[0].astype(int)
            offset = memories.loc[memories['mem_name'] == mem_name, 'address_offset'].iloc[0].astype(int)
            # not using factory for memories, Vivado having trouble recognizing it
            # print(f'        this.{mem_name.lower()} = uvm_mem::type_id::create("{mem_name.lower()}", this);', file=file)
            print(f'        this.{mem_name.lower()} = new("{mem_name.lower()}", {2**addr_width}, {data_width}, "{access}");', file=file)
            print(f'        this.{mem_name.lower()}.configure(this);', file=file)
            print(f'        this.default_map.add_mem(this.{mem_name.lower()}, {offset}, "{access}");', file=file)
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
            access = fields.loc[fields['field_name'] == field, 'access'].iloc[0]
            if width == 1:
                print(f'    logic        {field};', file=file)
            else:
                print(f'    logic [{width-1}:0] {field};', file=file)

            # generate set/clear bits for W1C fields
            if access == 'W1C':
                if width == 1:
                    print(f'    logic        {field}_set;', file=file)
                    print(f'    logic        {field}_clear;', file=file)
                else:
                    print(f'    logic [{width-1}:0] {field}_set;', file=file)
                    print(f'    logic [{width-1}:0] {field}_clear;', file=file)


        print('', file=file)
        is_writeable = (fields['access'] == 'W1C') | (fields['access'] == 'RW')
        print('    modport WR_BUS_IF (', file=file)
        for field in fields[is_writeable]['field_name']:
            access = fields.loc[fields['field_name'] == field, 'access'].iloc[0]
            if access == 'RW':
                print(f'        output {field};', file=file)
            elif access == 'W1C':
                print(f'        output {field}_set;', file=file)
                print(f'        input  {field};', file=file)
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

        print(file=file)
        is_w1c = fields['access'] == 'W1C'
        for field in fields[is_w1c]['field_name']:
            print(f'    modport CLEAR_{field} (output {field}_clear);', file=file)

        print('\nendinterface', file=file)


def remove_generated_files():
    '''
    Removes all generated files before regeneration
    '''
    if os.path.isfile(REG_IF_PATH):
        os.remove(REG_IF_PATH)
    if os.path.isfile(REGISTERS_RTL_PATH):
        os.remove(REGISTERS_RTL_PATH)
    if os.path.isfile(MEMORIES_RTL_PATH):
        os.remove(MEMORIES_RTL_PATH)
    if os.path.isfile(RAL_DUT_CONFIG_PATH):
        os.remove(RAL_DUT_CONFIG_PATH)
    if os.path.isfile(REG_MAP_CSV_PATH):
        os.remove(REG_MAP_CSV_PATH)
    if os.path.isfile(FIELDS_CSV_PATH):
        os.remove(FIELDS_CSV_PATH)
    if os.path.isfile(MEMORIES_CSV_PATH):
        os.remove(MEMORIES_CSV_PATH)


def generate_register_rtl(fields_df):
    '''
    Generates registers.sv file at the defined REGISTERS_RTL_PATH path

    Arguments:
        fields_df   : DataFrame : register fields
    '''
    with open(REGISTERS_RTL_PATH, 'w') as file:
        print('module registers(', file=file)
        print('    reg_if              i0,', file=file)
        print('    input  logic        clk,', file=file)
        print('    input  logic        rst_b,', file=file)
        print(f'    input  logic [{ADDR_WIDTH-1}:0] bus_if_wr_addr,', file=file)
        print(f'    input  logic [{FIELD_WIDTH-1}:0] bus_if_wr_data,', file=file)
        print(f'    input  logic        bus_if_wr_en,', file=file)
        print(f'    input  logic [{ADDR_WIDTH-1}:0] bus_if_rd_addr,', file=file)
        print(f'    output logic [{FIELD_WIDTH-1}:0] bus_if_rd_data,', file=file)
        print(f'    input  logic        bus_if_rd_en,', file=file)
        print(');', file=file)

        # generate RW registers
        print(f'\n    // generated RW register write logic', file=file)
        filt = fields_df['access'] == 'RW'
        for field_name in fields_df[filt]['field_name']:
            field_row = fields_df.loc[fields_df['field_name'] == field_name, :]
            reset_value = field_row['reset_value'].iloc[0]
            field_address = field_row['reg_address'].iloc[0]
            lsb_position = field_row['lsb_bit_position'].iloc[0]
            field_width = field_row['width'].iloc[0]
            print('    always_ff(@posedge clk) begin', file=file)
            print('        if (!rst_b)', file=file)
            print(f'            i0.{field_name} <= \'d{reset_value};', file=file)
            print(f'        else if (bus_if_wr_en && (bus_if_wr_addr == \'d{field_address}))', file=file)
            if field_width == 1:
                print(f'            i0.{field_name} <= bus_if_wr_data[{lsb_position}]', file=file)
            else:
                print(f'            i0.{field_name} <= bus_if_wr_data[{lsb_position + field_width - 1}:{lsb_position}]', file=file)
            print('    end', file=file, end='\n\n')

        print(f'\n    // generated W1C register set/clear logic', file=file)
        filt = fields_df['access'] == 'W1C'
        for field_name in fields_df[filt]['field_name']:
            field_row = fields_df.loc[fields_df['field_name'] == field_name, :]
            reset_value = field_row['reset_value'].iloc[0]
            field_address = field_row['reg_address'].iloc[0]
            lsb_position = field_row['lsb_bit_position'].iloc[0]
            field_width = field_row['width'].iloc[0]
            print('    always_ff(@posedge clk) begin', file=file)
            print('        if (!rst_b)', file=file)
            print(f'            i0.{field_name} <= \'d{reset_value};', file=file)
            print(f'        else if (bus_if_wr_en && (bus_if_wr_addr == \'d{field_address}))', file=file)
            if field_width == 1:
                print(f'            i0.{field_name} <= (i0.{field_name} & (~bus_if_wr_data[{lsb_position}])) | (i0.{field_name}_set);', file=file)
            else:
                print(f'            i0.{field_name} <= (i0.{field_name} & (~bus_if_wr_data[{lsb_position + field_width - 1}:{lsb_position}])) | (i0.{field_name}_set);', file=file)
            print('        else', file=file)
            print(f'            i0.{field_name} <= (i0.{field_name}) | (i0.{field_name}_set);', file=file)
            print('    end', file=file, end='\n\n')

        print('    // synchronous readback data', file=file)
        print('    always_ff @(posedge clk) begin', file=file)
        print('        if (!rst_b)', file=file)
        print('            bus_if_rd_data <= \'0;', file=file)
        print('        else if (bus_if_rd_en) begin', file=file)
        print('            case (bus_if_rd_addr)', file=file)
        print_registers_to_rtl(file)
        print('                default: bus_if_rd_data <= \'d0;', file=file)
        print('            endcase', file=file)
        print('        end else', file=file)
        print('            bus_if_rd_data <= \'0;', file=file)
        print('    end', file=file)

        print('endmodule', file=file)


def print_registers_to_rtl(file):
    '''
    Prints the register map to RTL to be able to read it back

    Arguments:
        file : file IO : file to which to write RTL
    '''
    reg_map = pd.read_csv(REG_MAP_CSV_PATH)
    for idx, row in reg_map.iterrows():
        print(f'                {row['address']} : bus_if_rd_data <= {FIELD_WIDTH}\'', file=file, end='')
        print('{', file=file, end='')
        # pdb.set_trace()
        for i in range(FIELD_WIDTH - 1, -1, -1):
            field = row[str(i)]
            if (field == 'reserved'):
                print(f'1\'b0', end='', file=file)
            else:
                print(f'i0.{field}', end='', file=file)
            if i > 0:
                print(f', ', file=file, end='')
        print('};', file=file)


def main():
    remove_generated_files()
    fields_json = parse_registers_json(FIELDS_PATH)
    fields_df = gen_fields_sheet(fields_json)
    memories_df = gen_memories_sheet(MEMORIES_PATH, True)
    gen_field_map(fields_df)
    generate_ral_config_file(fields_df, memories_df)
    generate_interface_file(fields_df)
    generate_register_rtl(fields_df)


if __name__ == '__main__':
    main()
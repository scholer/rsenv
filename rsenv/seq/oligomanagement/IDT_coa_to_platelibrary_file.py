"""

Simple script to convert IDT's "CoA" espec files to my standard plate library format:

Note: IDT has two "espec" file formats:
* CoA files, named `coa.csv` (I typically rename these `coa-<order number>.csv`).
* Excel files, named `RasmusPeterThomsen<order number>.xlsx`

The IDT Excel/xlsx files contains the following additional columns compared to the coa.csv files:
* Plate Name
* Payment Method
* Plate Barcode
* Well Barcode
* Measured Molecular Weight

But is missing the `Bases` column



Renamed columns:
* "Anhydrous Molecular Weight" is termed "Calculated Molecular Weight" in the Excel .xlsx files.


IDT also has "QC" files, which contains PDF files with the ESI mass-spec results.



Differences:
* The columns and column order is different between the two.
* IDT uses comma-separated values (csv), I prefer tab-separated values (tsv).
    After all, "tab" is used to *tabulate* values in a table. (*TAB*le).

function purify_sequence(sequence) {
  /\s*/gi, ""  -> remove whitespace
  /\/\w*\//gi, "" -> remove IDT mods, e.g. '/5pCy3/'
  /[^ATGCatgc]/gi -> remove anything that isn't ATGCatgc
  return sequence.replace(/\s*/gi, "").replace(/\/\w*\//gi, "").replace(/[^ATGCatgc]/gi)
}
function number_of_bases(sequence) {
  return purify_sequence(sequence).length
}
"""


import os
import sys
import re
# from types import Iterator, Optional
from typing import Iterable, Optional, List
from collections import OrderedDict, defaultdict
from pprint import pprint
import pandas as pd
import click
import fire

from rsenv.utils.cli_cmd_utils import create_click_cli_command


IDT_MOD_REGEX = re.compile(r"\/\w*\/")
CONVERT_BASE_TO_DNA = dict(zip("ATGCUatgcu", "ATGCTatgct"))

column_mapping_coa = OrderedDict({
    # Library-col:  IDT column name (after processing and updates)

    # Basic plate and oligo information:
    'Plate-name': 'Plate Name',  # Not present in native IDT coa.csv, has to be added manually.
    'Position': 'Well Position',
    'Oligo-name': 'Sequence Name',
    'Sequence': 'Sequence',
    'Length': 'Bases',

    # Oligo conc/amount/volume and status:
    'Conc/uM': 'Conc',
    'Amount/nmol': 'nmoles',
    'Volume/ul': 'Volume',
    'Volume-used/ul': 'Volume-used/ul',
    'Status': 'Status',  # "ok/depleted/dried-out/discarded"

    # Physical properties
    'Ext.coeff': 'Extinction Coefficient',
    'MW': 'Anhydrous Molecular Weight',  # is 'Calculated Molecular Weight' in xlsx
    'ATGC-Sequence': 'ATGC-Sequence',  # Sequence, in DNA-bases, with all modification annotations removed.

    # Experiment information:
    'Date': 'Date',
    'ExpID': 'ExpID',
    'Notes': 'Notes',

    # Vendor oligo ID information:
    'Vendor': 'Vendor',
    'Order-number': 'Sales Order #',
    'Vendor-oligo-id': 'Reference #',
    'Vendor-plate-barcode': 'Plate Barcode',
})

column_mapping_xlsx = OrderedDict({
    # Library-col:  IDT column name (after processing and updates)

    # Basic plate and oligo information:
    'Plate-name': 'Plate Name',  # Not present in native IDT coa.csv, has to be added manually.
    'Position': 'Well Position',
    'Oligo-name': 'Sequence Name',
    'Sequence': 'Sequence',
    'Length': 'Bases',

    # Oligo conc/amount/volume and status:
    'Conc/uM': 'Measured Concentration µM ',  # with space, it seems. Sloppy.
    'Amount/nmol': 'nmoles',
    'Volume/ul': 'Final Volume µL ',
    'Volume-used/ul': 'Volume-used/ul',
    'Status': 'Status',  # "ok/depleted/dried-out/discarded"

    # Physical properties
    'Ext.coeff': 'Extinction Coefficient L/(mole·cm)',
    'MW': 'Calculated Molecular Weight',
    'ATGC-Sequence': 'ATGC-Sequence',  # Sequence, in DNA-bases, with all modification annotations removed.

    # Experiment information:
    'Date': 'Date',
    'ExpID': 'ExpID',
    'Notes': 'Notes',

    # Vendor oligo ID information:
    'Vendor': 'Vendor',
    'Order-number': 'Sales Order #',
    'Vendor-oligo-id': 'Reference #',
    'Vendor-plate-barcode': 'Plate Barcode',
})

column_mapping_coa_keys = list(column_mapping_coa.keys())
column_mapping_xlsx_keys = list(column_mapping_xlsx.keys())
try:
    assert column_mapping_coa_keys == column_mapping_xlsx_keys
except AssertionError as exc:
    print("ERROR: library columns mis-match:")
    print(" - column_mapping_coa:\n", column_mapping_coa_keys)
    print(" - column_mapping_xlsx:\n", column_mapping_xlsx_keys)
    print(" - columns in xlsx but not coa:\n", [c for c in column_mapping_xlsx_keys if c not in column_mapping_coa_keys])
    print(" - columns in coa but not xlsx:\n", [c for c in column_mapping_coa_keys if c not in column_mapping_xlsx_keys])
    raise exc


def log(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs, )


def get_dna_sequence_nomods(seq, mod_regex=None):
    if mod_regex is None:
        mod_regex = IDT_MOD_REGEX
    seq = seq.replace(" ", "")
    seq = IDT_MOD_REGEX.sub("", seq)
    seq = "".join(CONVERT_BASE_TO_DNA.get(b, '') for b in seq)
    return seq


def convert_idt_coa_to_platelibrary_tsv(
        *input_files: str,  # Note: You have to do this to create nice fire CLI, type annotations alone doesn't work.
        # output_file_format="{fnroot}.tsv",
        # output_file_format="{order_number}-{plate_name}.tsv",
        # output_file_format="{vendor}-{order_number}.tsv",
        # output_file_format="{vendor}-{order_number}_{plate_name}.tsv",
        output_file_format: str="{plate_name}.tsv",
        # output_file_format="{plate_name} ({vendor}-{order_number}).tsv",
        # output_file_format="{expid}_{date}_{vendor}-{order_number}_{plate_name}.tsv",
        plate_name: str="", vendor: str="IDT", date: str="", expid: str="", notes: str="", order_number: str="",
        overwrite: str='Ask',  # Specify answer for "overwrite column" question, e.g. 'Ask', 'No', 'Yes', 'Empty'
        use_filename_as_platename: bool=False,
        group_by_plate: bool=True,
        sep: str="\t",
) -> None:
    """ Convert an IDT espec file (coa.csv or xlsx) to a library tsv file.
     The plate-library.tsv files has standardized columns and a few processed
     fields (e.g. cleaned "ATGC-sequence", and "Length")

    Args:
        input_files: One or more espec files from the plate vendor (or created by you, if needed).
        output_file_format: Format string specifying how to generate the output filename.
        plate_name: Specify default value for "Plate-name" column, if not available in the input file.
        vendor: Specify default value for "Vendor" column, if not available in the input file.
        order_number: Specify default value for "Order-number" column, if not available in the input file.
        date:  Specify default value for "Date" column, if not available in the input file.
        expid: Specify default value for "ExpID" column, if not available in the input file.
        notes: Specify default value for "Notes" column, if not available in the input file.
        overwrite: Overwrite existing values in input file with the given default column value
            for Vendor/Order-number/Date/ExpID/Notes. Recognized `overwrite` values are:
            "Yes" (overwrite everything), "No" (don't overwrite anything), and "Empty" (overwrite empty cells).
        use_filename_as_platename: For each input file, use filename (w/o ext) as default "Plate-name" column value.
        group_by_plate: Whether to group input data by Plate-name before saving.
            You should add {plate_name} to the output filename format, otherwise plates will overwrite each other.
        sep: The separator to use when saving output file (default "\t" for tsv files, comma "," for csv files).

    Returns:
        None

    """

    if sep == "TAB":
        sep = "\t"
    if sep == "COMMA":
        sep = ","
    if sep == "SEMICOLON":
        sep = ";"
    for input_file in input_files:
        log("Processing file:", input_file)
        absdirname = os.path.dirname(os.path.abspath(input_file))
        fnroot, fnext = os.path.splitext(input_file)
        fnbase_no_ext =  os.path.basename(fnroot)
        input_format = fnext.strip('.').lower()
        if use_filename_as_platename:
            plate_name = fnbase_no_ext
        # input_df = pd.read_csv(input_file) if input_format == 'csv' else pd.read_excel(input_file)
        input_df = pd.read_excel(input_file) if input_format == 'xlsx' else pd.read_csv(input_file)
        column_mapping = column_mapping_xlsx if input_format == 'xlsx' else column_mapping_coa

        print("Input file columns:", input_df.columns, sep="\n")
        # print("Input file head:")
        # print(input_df.head())
        print("Column mapping:")
        pprint(column_mapping)

        # FIXES:
        for col, default_value in zip(
                ('Plate-name', 'Vendor', 'Date', 'ExpID', 'Notes'),  # , 'Sales Order'),
                (plate_name, vendor, date, expid, notes)  # , order_number)
        ):
            if column_mapping[col] in input_df and default_value:
                print(f"Warning: `{column_mapping[col]}` column is present in the input file, "
                      f"but a default value `{default_value}` was also provided.")
                if overwrite is None or overwrite.lower() == 'ask':
                    answer = input("Overwrite existing data with the default value? [NO, Yes, Empty]") or 'No'
                else:
                    answer = overwrite
                if answer[0].lower() == 'y':
                    input_df[col] = default_value or ""
                elif answer[0].lower() == 'e':  # overwrite empty values
                    def is_none_or_empty_string(val):
                        # Maybe we don't want 0 (zero) to be an "empty value", but only "" (empty stirng) and None
                        return val is None or val == ""
                    # We use a mask to access empty rows (cells):
                    input_df[col, input_df[col].map(is_none_or_empty_string)] = default_value
            else:
                print(f"Adding column to input table: {col} = {default_value}")
                input_df[col] = default_value or ""

        def fix_seq(seq):
            return seq.strip().replace(" ", "")
        # For series, we use Series.map() for elementwise apply; for dataframes we use DataFrame.applymap()
        input_df['Sequence'] = input_df['Sequence'].map(fix_seq)

        input_df['ATGC-Sequence'] = input_df['Sequence'].map(get_dna_sequence_nomods)

        n_bases = input_df['ATGC-Sequence'].map(len)
        if column_mapping['Length'] in input_df:
            print(f"'Length' column ('{column_mapping['Length']}') already present in input file, checking values...")
            # Check that the expected lengths match:
            # Have to use pd.Series.all() to get a defined Truth value:
            if not (n_bases == input_df[column_mapping['Length']]).all():
                print("WARNING: The sequence length calculated from cleaned sequence "
                      "doesn't match the existing information in the input file.")
        else:
            print(f"'Length' column ('{column_mapping['Length']}') NOT present in input file, adding...")
            input_df[column_mapping['Length']] = n_bases

        # Add additional oligo-plate-library fields:
        input_df['Volume-used/ul'] = 0
        input_df['Status'] = ""  # "ok/depleted/dried-out/discarded"

        output_df = pd.DataFrame.from_dict(OrderedDict([
            (output_col, input_df[input_col]) for output_col, input_col in column_mapping.items()]))

        grouped_df = output_df.groupby('Plate-name')
        if group_by_plate:
            for plate_name, df_group in grouped_df:
                order_number = df_group['Order-number'][0]
                output_filename = output_file_format.format(**locals())
                print("Output filename:", output_filename)
                print(f"Exporting {len(output_df)} rows to file:", output_filename)
                output_df.to_csv(output_filename, sep=sep, index=False)
        else:
            plate_name = output_df['Plate-name'][0]
            order_number = output_df['Order-number'][0]
            output_filename = output_file_format.format(**locals())
            print("Output filename:", output_filename)
            print(f"Exporting {len(output_df)} rows to file:", output_filename)
            output_df.to_csv(output_filename, sep=sep, index=False)


# Create a very basic click CLI from a regular python function:
# convert_IDT_espec_to_platelibrary_file_cli = create_click_cli_command(
#     convert_idt_coa_to_platelibrary_tsv,
#     arg_spec={'input_files': {'nargs': -1}}
# )


# Alternatively, use fire instead of click:
def convert_IDT_espec_to_platelibrary_file_cli():

    # This should "just work", with the right function annotations.
    # import fire
    # fire.Fire(convert_idt_coa_to_platelibrary_tsv)

    # defopt:
    # import defopt
    # defopt.run(convert_idt_coa_to_platelibrary_tsv)  # Seems to require docstring parameter type annotations.

    # clize:
    import clize
    clize.run(convert_idt_coa_to_platelibrary_tsv)
    # Note: I'm using a patched version of clize (runner.py:303, see github issue #37)


# # Create a more customized CLI:
# @click.command()
# @click.argument('input-files', nargs=-1)
# @click.option('--output-file-format')
# @click.option('--plate-name')
# @click.option('--order-number')
# def convert_IDT_espec_to_platelibrary_file_cli(
#         input_files,
#         output_file_format="{dirname}/{fnbase_no_ext}.tsv",
#         plate_name="", vendor="IDT", date="", expid="", notes="", order_number="",
#         overwrite='Ask',  # Provide constant answer for "overwrite column" question, e.g. 'Ask', 'No', 'Yes', 'Empty'
#         use_filename_as_platename=False,
#         group_by_plate=True,
#         sep="\t",
# ):
#     convert_idt_coa_to_platelibrary_tsv(
#         input_files=input_files,
#         output_file_format=output_file_format,
#         plate_name=plate_name
#     )




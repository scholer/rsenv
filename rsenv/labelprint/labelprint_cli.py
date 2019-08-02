# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
r"""

CLI for printing labels.



Examples:
---------

First, let's specify the label template file so we don't have to do that every time:

    SET DROPBOX_PATH=C:\Users\au206270\Dropbox
    SET ZPL_TEMPLATES_DIR=%DROPBOX_PATH%\_experiment_data\experiment-aux-files\Label-print\Zebra-label-printing\zpl-templates
    SET ZPL_TEMPLATE_FILE=%DROPBOX_PATH%\_experiment_data\experiment-aux-files\Label-print\Zebra-label-printing\zpl-templates\JTTA-172_SampleID-Date-Description-lidbarcode_03_labeltemplate.zpl
    SET EXAMPLE_DATA_DIR=C:\Users\au206270\Dev\rsenv\examples\example_data\labelprint

Print, specifying data as command line arguments:

    print-zpl-labels
        --label-template-file "%ZPL_TEMPLATES_FILE%
        --source-type cmdarg
        --data-args "sampleid:RS123d1,datestr:20190729,sampledesc:Sample Test description;\
                     sampleid:RS123d2,datestr:20190728,sampledesc:Sample 2 Description"
        --sep=, --eol-char=";"

Specifying data as cmdargs, but using `fieldnames` to make it easier to write multiple rows:

    print-zpl-labels ^
        --label-template-file "%ZPL_TEMPLATES_FILE%
        --source-type cmdarg ^
        --fieldnames "datestr,sampleid,sampledesc" ^
        --data-args "20190729,RS123d1,Sample Test description;20190728,RS123d2,Sample 2 Description" ^
        --sep=, --eol-char=";" ^

Specify formulas, which calculate the total length of datestr+sampleid+sampledesc (`totlen`),
and a suitable datamatrix barcode size (`dmsize`):

    print-zpl-labels
        --label-template-file "%ZPL_TEMPLATES_FILE%
        --source-type cmdarg
        --fieldnames "datestr,sampleid,sampledesc"
        --data-args "20190729,RS123d1,Sample Test description;190728,RS123d2,S2Descr"
        --sep=, --eol-char=";"
        --verbose 1
        --do-print False
        --printer "\\localhost\usb001_generic_text_printer"
        --formulas "totlen=len(datestr)+len(sampleid)+len(sampledesc),dmsize=2 if totlen > 24 else 3"


Read from clipboard:

    print-zpl-labels --label-template-file "%ZPL_TEMPLATE_FILE%" --verbose 1 --do-print False --source-type clipboard


Read from csv file:

    print-zpl-labels --label-template-file "%ZPL_TEMPLATE_FILE%" --verbose 1 --do-print False --source-type csvfile
        --data-file data_content_header.tsv --sep=TAB

    print-zpl-labels --label-template-file "%ZPL_TEMPLATE_FILE%" --verbose 1 --do-print False --source-type csvfile
        --data-file data_content_header.csv --sep=,

    print-zpl-labels --label-template-file "%ZPL_TEMPLATE_FILE%" --verbose 1 --do-print False --source-type csvfile
        --fieldnames="datestr,sampleid,sampledesc"
        --data-file data_content_no_header.csv --sep=,


Read from stdin:

    print-zpl-labels --label-template-file "%ZPL_TEMPLATE_FILE%" --verbose 1 --do-print False
        --sep=,
        --fieldnames="datestr,sampleid,sampledesc"
        --source-type stdin  < data_content_no_header.csv


Note that using --formulas will simply `eval()` the given expressions.
NEVER accept formulas from an untrusted source! The input can run arbitrary commands on your system!

OBS: On Windows, ^ can be used for breaking command line input over multiple lines.

"""

import os
import sys
import io
from pprint import pprint, pformat
import click
import yaml
import fire

from .zpl import generate_zpl, check_forbidden_characters_in_data, DEFAULT_ZPL_PRINTER_CONFIG
from .windows_printing import print_content
from .datareader import data_from_args, data_from_clipboard, data_from_csv_file, \
    data_from_csv_content, data_from_stdin, get_formulas, eval_formulas


def print_zpl_labels(
        source_type: str = 'stdin',
        data_file=None,
        data_args=None,
        fieldnames=None,
        formulas=None,
        formulas_file=None,
        sep: str = "\t",
        eol_char: str = "\n",
        strip_whitespace=False,
        data_forbidden_chars="^~\\[]",
        assignment_char: str = ":",
        label_template_file=None,
        printerconfig_zpl=None,
        printerconfig_zpl_file=None,
        save_to_file=None,
        do_print=False,
        printer=None,
        print_method=None,
        verbose: int = 1,
) -> str:
    """ Generate ZPL file by combining input data with a ZPL template.

    Args:
        source_type: Where to get input data from, e.g. 'csvfile', 'clipboard', 'cmdarg', 'stdin'.
        data_file: Read input data (requires source_type='csvfile').
        data_args: Specify input data as command line argument.
        fieldnames: Specifies column/field names. If omitted, the fieldnames must be given
            by alternative means, e.g. a header row in the csv file, or using "field:value"
            in data_args.
        formulas: Specify formulas, which are fields where the value is derived from existing fields
            by evaluating the given expression.
        formulas_file: Read formulas from a file (may be easier than specifying them
            on the command line every time).
        sep: The character used to separate fields in each row.
        eol_char: The character used to separate one line from the next.
            The default is obviously a newline '\n', but can be changed to e.g. semi-colons.
        strip_whitespace: If True, will strip whitespace from both fieldnames and values when reading data.
            This is useful if you like to use e.g. spaces to align the fields in the input data.
        data_forbidden_chars: Specify invalid data characters
            (some characters do not play well with the ZPL template without careful escaping).
        assignment_char: Assignment character used when specifying data on the command line, for source_type='cmdarg'.
        label_template_file: The template to use for each printed label.
        printerconfig_zpl: Specify the printerconfig_zpl content directly.
            If printerconfig_zpl is None (default), it will try to get printerconfig_zpl from printerconfig_zpl_file.
        printerconfig_zpl_file: The ZPL printer config. This is typically just a single ZPL
            command set, added at the top of the zpl file that is sent to the printer.
            printerconfig_zpl_file is only loaded IF `printerconfig_zpl` is None.
            If both `printerconfig_zpl` and `printerconfig_zpl_file` are None,
            a module-default value is used for convenience. To disable sending any printerconfig ZPL commands at all,
            you should set `printerconfig_zpl=""` when calling this function.
        save_to_file: Save ZPL output to file. May be useful for debugging.
        do_print: Enable or disable actual printing of the generated ZPL content.
        printer: The printer to print the ZPL content to.
            OBS! The printer should be specified as a "fully-qualified" path, and should not
            contain any spaces or other weird characters.
        print_method: The method used to print the ZPL content.
            You can use this to customize which command is used to send the file to the printer.
            Some methods have different quirks, so using a non-default method may give better results.
        verbose: If you would like the program to display more (debug) information while it is
            processing the data and generating and priting the ZPL content,
            you can set verbose to a value above zero.

    Returns:
        The generated zpl_content (str).

    # TODO: Use a generator pattern for input data, so you can stream data to the printer.
    # Note that this will make it a little hard to determine when the last label is printed,
    # so it may be more trouble than is worth it, at least until you have an actual use case.
    """

    if sep == "\\t" or sep == "TAB":
        print(f"Converting escaped sep={sep!r} to regular tab character '\t'.", file=sys.stderr)
        sep = "\t"

    # 1. Read input data
    if verbose:
        print(f"Reading input data from {source_type} using sep={sep!r}...", file=sys.stderr)
    if source_type == 'csvfile':
        if not data_file:
            raise ValueError(f"`data_file` ({data_file}) must be specified when `source_type` is 'csvfile'.")
        data = data_from_csv_file(data_file, fieldnames=fieldnames, sep=sep)
    elif source_type == 'clipboard':
        data = data_from_clipboard(fieldnames=fieldnames, sep=sep)
    elif source_type == 'stdin':
        data = data_from_stdin(fieldnames=fieldnames, sep=sep)
    elif source_type == 'cmdarg':
        # `data_args` is a list of row-specifiers, e.g. `["first:Hej,Second:Der"]`
        data = data_from_args(
            data_args, fieldnames=fieldnames, sep=sep, eol_char=eol_char, assignment_char=assignment_char)
    else:
        raise ValueError(f"Unrecognized value {source_type!r} for argument `source_type`.")

    if verbose:
        print("Input data:", file=sys.stderr)
        print(pformat(data), file=sys.stderr)

    # Read and evaluate formulas, if given (either as argument or in file)
    if formulas and isinstance(formulas, str):
        formulas = get_formulas(formulas, sep=sep, format="key=expression")
    else:
        formulas = {}
    if formulas_file:
        file_formulas = yaml.safe_load(open(formulas_file))
        for key, expr in file_formulas:
            formulas.setdefault(key, expr)
    if formulas:
        eval_formulas(data=data, formulas=formulas, combined=True, inplace=True)
        if verbose:
            print("Data (after evaluating formulas):", file=sys.stderr)
            print(pformat(data), file=sys.stderr)

    if strip_whitespace:
        if verbose:
            print("Stripping leading/trailing whitespace from fieldnames and values...", file=sys.stderr)
        data = [{key.strip(): val.strip() if isinstance(val, str) else val for key, val in row.items()}
                for row in data]

    # Check the data for forbidden characters:
    check_forbidden_characters_in_data(data, do_raise=True, forbidden_chars=data_forbidden_chars)

    # 2. Read zpl templates and printer config:
    if label_template_file is None:
        raise ValueError("`label_template_file` must be specified, either on command line or in config.")
        # Actually, we just use program default for now, but may be required later.
    if label_template_file == "-":
        label_template = sys.stdin.read()
    else:
        label_template = open(os.path.expanduser(label_template_file)).read()

    if printerconfig_zpl is None:
        if printerconfig_zpl_file:
            printerconfig_zpl = open(os.path.expanduser(printerconfig_zpl_file)).read()
        else:
            printerconfig_zpl = DEFAULT_ZPL_PRINTER_CONFIG

    zpl_content = generate_zpl(data, label_template=label_template, printconfig=printerconfig_zpl)

    if verbose:
        print("\nZPL content generated OK.", file=sys.stderr)

    if save_to_file:
        if save_to_file == "-":
            print("Writing zpl content to stdout...", file=sys.stderr)
            sys.stdout.write(zpl_content)
        else:
            with open(save_to_file, 'wb') as f:
                print(f"Writing zpl content to file {save_to_file} ...", file=sys.stderr)
                f.write(zpl_content)

    if do_print:
        if verbose:
            print(f"Printing zpl content to printer {printer} using method {print_method} ...", file=sys.stderr)
        print_content(zpl_content, printer=printer, method=print_method, verbose=verbose)

    return zpl_content


def print_zpl_labels_cli():
    # fire.Fire will print the return value to stdout.
    fire.Fire(print_zpl_labels)
    # TODO: Switch from using fire to click.

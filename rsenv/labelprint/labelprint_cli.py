# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

CLI for printing labels.



Examples:

    SET ZPL_TEMPLATES_PATH="D:\Dropbox\_experiment_data\experiment-aux-files\Label-print\Zebra-label-printing\zpl-templates"

    print-zpl-labels --source-type cmdarg
        --data-args "sampleid:RS123d1,datestr:20190729,sampledesc:Sample Test description;\
                     sampleid:RS123d2,datestr:20190728,sampledesc:Sample 2 Description"
        --sep=, --eol-char=";"
        --label-template-file "%ZPL_TEMPLATES_PATH%/JTTA-172_SampleID-Date-Description-lidbarcode_03_labeltemplate.zpl"


    print-zpl-labels
        --source-type cmdarg
        --fieldnames "datestr,sampleid,sampledesc"
        --data-args "20190729,RS123d1,Sample Test description;20190728,RS123d2,Sample 2 Description"
        --sep=, --eol-char=";"
        --label-template-file "%ZPL_TEMPLATES_PATH%/JTTA-172_SampleID-Date-Description-lidbarcode_03_labeltemplate.zpl"


"""

import os
import sys
import click

from .zpl import generate_zpl
from .windows_printing import print_content
from .datareader import data_from_args, data_from_clipboard, data_from_csv_file, data_from_csv_content, data_from_stdin


def print_zpl_labels(
        source_type='stdin',
        data_file=None, fieldnames=None,
        data_args=None,
        sep="\t",
        eol_char="\n",
        assignment_char=":",
        label_template_file=None,
        printerconfig_zpl_file=None,
        save_to_file=None,
        do_print=False,
        printer=None,
        print_method="shell-print",
        verbose=1,
):

    # 1. Read input data
    if source_type == 'csvfile':
        data = data_from_csv_file(data_file, fieldnames=fieldnames, sep=sep)
    elif source_type == 'clipboard':
        data = data_from_clipboard(fieldnames=fieldnames, sep=sep)
    elif source_type == 'stdin':
        if verbose:
            print("Reading input data from stdin...", file=sys.stderr)
        data = data_from_stdin(fieldnames=fieldnames, sep=sep)
    elif source_type == 'cmdarg':
        # `data_args` is a list of row-specifiers, e.g. `["first:Hej,Second:Der"]`
        data = data_from_args(
            data_args, fieldnames=fieldnames, sep=sep, eol_char=eol_char, assignment_char=assignment_char)
    else:
        raise ValueError(f"Unrecognized value {source_type!r} for argument `source_type`.")

    if verbose:
        print("Input data:", file=sys.stderr)
        print(data, file=sys.stderr)

    # 2. Read zpl templates and printer config:
    if label_template_file is None:
        raise ValueError("`label_template_file` must be specified, either on command line or in config.")
        # Actually, we just use program default for now, but may be required later.
    if label_template_file == "-":
        label_template = sys.stdin.read()
    else:
        label_template = open(os.path.expanduser(label_template_file)).read()

    if printerconfig_zpl_file:
        printerconfig_zpl = open(os.path.expanduser(printerconfig_zpl_file)).read()
    else:
        printerconfig_zpl = ""

    zpl_content = generate_zpl(data, label_template=label_template, printconfig=printerconfig_zpl)

    if save_to_file:
        if save_to_file == "-":
            sys.stdout.write(zpl_content)
        else:
            with open(save_to_file, 'wb') as f:
                f.write(zpl_content)

    if do_print:
        print_content(zpl_content, printer=printer, method=print_method)

    return zpl_content


def print_zpl_labels_cli():
    import fire
    fire.Fire(print_zpl_labels)

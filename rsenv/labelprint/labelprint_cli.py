# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

CLI for printing labels.

"""

import sys

from .zpl import generate_zpl
from .windows_printing import print_content


def print_zpl_labels(
        source_type='csv',
        data_file=None, header=None, data_args=None,
        sep="\t",
        label_template_file=None, printerconfig_zpl_file=None,
        save_to_file=None,
        do_print=False,
        printer=None,
        print_method="shell-print",
        verbose=1,
):

    # 1. Read input data
    if source_type == 'csv':
        data = data_from_csv(data_file, header=header, sep=sep)
    elif source_type == 'clipboard':
        data = data_from_clipboard(header=header, sep=sep)
    elif source_type == 'stdin':
        data = data_from_stdin(header=header, sep=sep)
    elif source_type == 'cmdarg':
        data = data_from_args(data_args, header=header, sep=sep)

    # 2. Read zpl templates and printer config:
    if label_template_file:
        if label_template_file == "-":
            label_template = sys.stdin.read()
        else:
            label_template = open(label_template_file).read()
    if printerconfig_zpl_file:
        printerconfig_zpl = open(printerconfig_zpl_file).read()
    else:
        printerconfig_zpl = ""

    zpl_content = generate_zpl(data, label_template=label_template, printconfig=printerconfig_zpl)

    if save_to_file:
        with open(save_to_file, 'wb') as f:
            f.write(zpl_content)

    if do_print:
        print_content(zpl_content, printer=printer, method=print_method)

    return zpl_content



def data_from_csv(filename, header=None, sep=None):
    pass

def data_from_clipboard(header=None, sep=None):
    pass

def data_from_stdin(header=None, sep=None):
    pass

def data_from_args(data_args, header=None, sep=None):
    pass

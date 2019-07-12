# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Printing ZPL:



"""


zpl_printer_config = """

^FX[ Printer configuration ]^FS

^XA
~TA000
^MMT
^MNW
^MTT

^CI0
^JMA
~JSN
^JUS

^LH0,0
^LT0
^LS0
^LRN
^PON
^PMN

^PR2,2
~SD15
^XZ

"""


zpl_label_template = """

^FX[ Label Format ]^FS

^XA
^MMT
^PW395
^LL0153
^LS0

^FO294,28^GE88,88,1^FS

^FO15,9^GB254,126,1^FS


^FO20,15
^A0N,26,26
^FB140,2,0,L,0
^FD{sampleid}
^FS


^FO150,15
^A0N,26,26
^FB115,2,0,R,0
^FD{datestr}
^FS


^FT20,130
^A0N,28,28
^FB250,3,0,C,0
^FD{sampledesc}
^FS


^BY48,48
^FT311,100
^BXN,3,200,0,0,1,~,1
^FH\^FD{lid_barcode}
^FS


^PQ1,0,1,Y

^FX[ Omit XB for the last command ]^FS
^XB

^XZ
"""


def format_single_label(values, label_template=None, is_last=True):

    if label_template is None:
        label_template = zpl_label_template

    label = label_template.format(XB="" if is_last else "^XB", **values)
    return label


def generate_zpl(data, label_template=None, printconfig=None):

    if printconfig is None:
        printconfig = zpl_printer_config

    zpl_parts = [printconfig]

    n_rows = len(data)
    for i, row in enumerate(data, 1):
        zpl_parts.append(format_single_label(row, is_last=i == n_rows))

    zpl_content = "\n".join(zpl_parts)


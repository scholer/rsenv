# Copyright 2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>
"""

Module for generating ZPL labels by interpolating a pre-defined ZPL template with the given data.


OBS: Sorry, this module is not for actually generating ZPL labels "from scratch".

If you want to generate ZPL files that you can use as label templates (and for specifying
the ZPL printer config), you can use the following tools:

* ZebraDesigner or ZebraDesigner Pro (just print the label to file, then replace the text
    values with `{placeholder_names}`.

* http://labelary.com/viewer.html - this is an excellent and easy way to generate labels.

In the places where you would like to insert variable values, type `{placeholder_name}`.
For instance, if you would like to print 100 shipping labels, in the place where you
would like the street name to go, type `{street_name}`.
When you then


When you have a given ZPL label file, you need to do two things:

    * Open the zpl file in a text editor (Notepad++ or Sublime Text).
        If you are using http://labelary.com/viewer.html, you can opy/paste the ZPL commands
        to a new file using the text editor.
    * First, cut off the "printer configuration" part of the label and place it in a
        separate "printer_config.zpl" file. This part is only sent to the printer
        once for every job.
    * Second, replace the text values in the ZPL with `{placeholder_name}`,
        if you have not already done this when generating the label.
        (E.g. if you are using a zpl label that someone else made.)
        The text values are typically placed right after `^FD` or `^FO` commands.
        Only replace the text! Do no change anything else.



"""


DEFAULT_ZPL_PRINTER_CONFIG = """

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
~SD25
^XZ

"""


DEFAULT_ZPL_LABEL_TEMPLATE = """

^FX[ Label Format ]^FS
^FX[ PrintWidth is 395 dots = 49.375 mm = 1.944 in ]^FS
^FX[ LabelLength is 152 dots = 19.125 mm = 0.753 in ]^FS

^XA
^MMT
^PW395
^LL0153
^LS0


^FX[ Label alignment objects: rectangle and circle ]^FS

^FO15,9^GB254,126,1^FS
^FO294,28^GE88,88,1^FS


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


^FX[ Lid datamatrix barcode ]^FS

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

DEFAULT_VALUES = {}


def check_forbidden_characters_in_data(data, forbidden_chars="^~\\[]", do_raise=True):
    for i, row in enumerate(data):
        for key, value in row.items():
            value = f"{value}"  # Alternatively, only check strings?
            for c in forbidden_chars:
                if c in value:
                    msg = f"ERROR: Forbidden character '{c}' in row {i}, field '{key}': '{value}'."
                    print(msg)
                    if do_raise:
                        raise ValueError(msg)


def format_single_label(values, label_template=None, is_last=True):

    if label_template is None:
        label_template = DEFAULT_ZPL_LABEL_TEMPLATE

    try:
        template_vars = DEFAULT_VALUES + values  # Dict addition operator only works for python 3.8+
    except TypeError:
        template_vars = DEFAULT_VALUES.copy()
        template_vars.update(values)
    label = label_template.format(XB="" if is_last else "^XB", **template_vars)
    return label


# TODO: Change this from 'generate_zpl' to a more accurate 'generate_zpl_from_template_and_data'.
def generate_zpl(data, label_template=None, printconfig=None):

    if printconfig is None:
        printconfig = DEFAULT_ZPL_PRINTER_CONFIG

    zpl_parts = [printconfig]

    n_rows = len(data)
    for i, row in enumerate(data, 1):
        row.setdefault('label_num', i)
        zpl_parts.append(format_single_label(row, label_template=label_template, is_last=i == n_rows))

    zpl_content = "\n".join(zpl_parts)
    return zpl_content

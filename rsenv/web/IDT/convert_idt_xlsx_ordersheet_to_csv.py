
"""
Convert xlsx files to csv.


Refs:
* https://openpyxl.readthedocs.io/en/default/
* http://www.python-excel.org/
* https://pypi.python.org/pypi/xlsx2csv   = no dependencies
* https://pypi.python.org/pypi/tablereader   - uses openpyxl
* https://github.com/pyexcel/pyexcel-cli

"""


import os
# import sys
import argparse
# from pyexcel import save_as
from openpyxl import load_workbook


def convert_xlsx_to_csv(inputfn, outputfn, sep_out="\t"):
    """Reformat input csv file, printing to outputfn."""

    # save_as(file_name=inputfn, dest_file_name=outputfn, dest_file_type='csv')
    wb = load_workbook(inputfn, read_only=True)
    wb.get_sheet_names()
    ws = wb.worksheets[1]
    print("Using worksheet '%s' in workbook '%s'" % (inputfn, ws.title))
    nlines = 0
    with open(outputfn, 'w') as fout:
        header_found = False
        for row in ws:
            row_values = [cell.value or "" for cell in row]
            if row[0].value == "Plate Name(s)":
                header_found
                headers = [cell.value or "" for cell in row]
                print("Found headers:", headers)
                fout.write(sep_out.join(headers) + '\n')
                header_found = True
                continue
            if not header_found:
                continue
            # Make sure to compare value..
            if not row[0].value or row[0].value == "Standard Plate Example":
                # Skip blank lines
                continue
            fout.write(sep_out.join(cell.value or "" for cell in row) + '\n')
            nlines += 1
    return nlines


def batch_convert(inputfiles, outputdir=None, fnfmt="{fnroot}.csv", read_stdin=False, write_stdout=False,
                  overwrite=True, discart=r'~$'):
    """Bulk reformatting of multiple input files."""

    if outputdir:
        outputdir = os.path.expanduser(outputdir)
        if not os.path.exists(outputdir):
            print("Creating output directory:", outputdir)
            os.mkdir(outputdir)
        elif not os.path.isdir(outputdir):
            print("\n\nERROR: outputdir %s exists but is not a directory, aborting!" % (outputdir,))
            return

    for inputfn in inputfiles:
        if inputfn.startswith('~') or inputfn.startswith('$') or inputfn.startswith('.'):
            # Dont want these:
            print("Ignoring file:", inputfn)
            continue
        if outputdir is None:
            fnroot, fnext = os.path.splitext(inputfn)
        else:
            fnroot, fnext = os.path.splitext(os.path.basename(inputfn))  # basename = "filename without directory"
        outputfn = fnfmt.format(fn=inputfn, fnroot=fnroot, ext=fnext)
        if outputdir:
            outputfn = os.path.join(outputdir, outputfn)

        print("outputfn:", outputfn)
        print("Converting xlsx file:", inputfn)
        nlines = convert_xlsx_to_csv(inputfn, outputfn)
        print(" - %04s lines written: %s" % (nlines, outputfn))


def make_parser(args):
    ap = argparse.ArgumentParser(prog="Reformat CSV")
    ap.add_argument("inputfiles", nargs="*")
    ap.add_argument("--outputdir")
    ap.add_argument("--fnfmt", default="{fnroot}.csv")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    return ap


def main(args=None):
    """Convert input files as specified by command line arguments. (main entry point)"""
    ap = make_parser(args)
    argns = ap.parse_args(args)

    batch_convert(argns.inputfiles, argns.outputdir, argns.fnfmt)


# run-alone entry point:
if __name__ == '__main__':
    main()

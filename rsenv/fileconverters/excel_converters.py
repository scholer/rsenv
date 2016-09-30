#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2016 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#




import os
# import sys
import argparse
import csv
# from pyexcel import save_as
from openpyxl import load_workbook


def convert_xlsx_to_csv(inputfn, outputfmt="{fnroot}_{sheetname}.csv",
                        sheets=None, overwrite=None,
                        usecsvmodule=False, sep_out=None, dialect="excel"):
    """Reformat input csv file, printing to outputfn."""
    # save_as(file_name=inputfn, dest_file_name=outputfn, dest_file_type='csv')
    wb = load_workbook(inputfn, read_only=True)
    wb.get_sheet_names()
    fnroot, ext = os.path.splitext(inputfn)
    if not usecsvmodule and sep_out is None:
        sep_out = '\t'
    nfiles = 0
    nbytes_tot = 0
    if sheets:
        # print("sheets:", sheets)
        sheet_idxs = set(sheets)
        for sheet in sheets:
            try:
                sheet_idxs.add(int(sheet))
            except ValueError:
                pass
        sheets = sheet_idxs
        # print("sheet_idxs:", sheet_idxs)
    for sheetidx, ws in enumerate(wb.worksheets, 1):
        if sheets and (sheetidx not in sheet_idxs and ws.title not in sheet_idxs):
            print("EXCLUDING sheet %02s: %s" % (sheetidx, ws.title))
            continue
        print("Using worksheet '%s' in workbook '%s'" % (ws.title, inputfn))
        outputfn = outputfmt.format(fnroot=fnroot, sheetname=ws.title)
        # TODO: Consider using csv module for proper quoting of cell values.
        if usecsvmodule:
            # If using csv module, files should be opened with newline='' to prevent inserting extra '\r'
            with open(outputfn, 'w', newline='') as fout:
                csvwriter = csv.writer(fout, dialect=dialect)
                rows = ((cell.value if cell.value is not None else "" for cell in row) for row in ws)
                # No, simply passing ws doesn't work because we need cell.value not cell.
                csvwriter.writerows(rows)  # Returns None
            print(" - %04s rows written to file %s." % (len(tuple(ws.rows)), outputfn))
        else:
            with open(outputfn, 'w') as fout:
                nbytes = fout.write("\n".join(
                    sep_out.join(str(cell.value if cell.value is not None else "") for cell in row) for row in ws) + '\n')
                nbytes_tot += nbytes
            print(" - %04s bytes written to file %s." % (nbytes, outputfn))
        nfiles += 1
    return nfiles


def batch_convert(inputfiles, outputdir=None, fnfmt="{fnroot}_{sheetname}.csv",
                  sep_out=None, dialect="excel", usecsvmodule=False,
                  sheets=None,
                  read_stdin=False, write_stdout=False,
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
        fnfmt = os.path.join(outputdir, fnfmt)

    print("Converting %s files, saving to outputdir '%s'" % (len(inputfiles), outputdir if outputdir else "."))
    for inputfn in inputfiles:
        if inputfn.startswith('~') or inputfn.startswith('$') or inputfn.startswith('.'):
            # Dont want these:
            print("Ignoring file:", inputfn)
            continue

        print("Converting xlsx file:", inputfn)
        print(" - outputfn:", fnfmt)
        nfiles = convert_xlsx_to_csv(
            inputfn, outputfmt=fnfmt,
            sep_out=sep_out, dialect=dialect, usecsvmodule=usecsvmodule,
            sheets=sheets, overwrite=overwrite
        )
        print(" - %04s files/sheets saved." % (nfiles,))



def make_parser(args):
    ap = argparse.ArgumentParser(prog="Reformat CSV")
    ap.add_argument("inputfiles", nargs="*")
    ap.add_argument("--outputdir")
    ap.add_argument("--fnfmt", default="{fnroot}_{sheetname}.csv")
    ap.add_argument("--sep_out")  #, default="\t")
    ap.add_argument("--dialect", default="excel")
    ap.add_argument("--sheets", nargs='*')
    ap.add_argument("--no-overwrite", action="store_false", dest="overwrite")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--read-stdin", action="store_true")
    ap.add_argument("--write-stdout", action="store_true")
    ap.add_argument("--usecsvmodule", action="store_true")

    return ap


def main(args=None):
    """Convert input files as specified by command line arguments. (main entry point)"""
    ap = make_parser(args)
    argns = ap.parse_args(args)

    # batch_convert(inputfiles=argns.inputfiles,
    #               outputdir=argns.outputdir,
    #               fnfmt=argns.fnfmt,
    #               sep_out=argns.sep_out,
    #               dialect=argns.dialect,
    #               overwrite=argns.overwrite,
    #               usecsvmodule=argns.usecsvmodule,
    #               sheets=argns.sheets
    #               )
    batch_convert(**vars(argns))

    print("\nDone!\n")


# run-alone entry point:
if __name__ == '__main__':
    main()

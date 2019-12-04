#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##

# pylintxx: disable-msg=C0103,C0301,C0302,R0201,R0902,R0904,R0913,W0142,W0201,W0221,W0402
# pylint: disable=C0103,C0111,R0913,W0142

"""

Extract sequences from cadnano staples export files (*.oligos.csv)
and produce an IDT-friendly order file:
    Name    Sequence    [scale] [purification/services]

Example usage:
    # Read all oligos from cadnano export files matching the pattern *.staples.csv in example_files/,
    # replacing "CircFoldback_0" with "CircFB" in row["Design"], and
    # output order rows to the default output file, overwriting if nessecary and use verbosity=2 :
    $> python cadnano_agg_order.py -y example_files/*.staples.csv -v -v -r Design CircFoldback_0 CircFB

    # Read oligos from mydesign.staples.csv, adding "20nmU" as scale and "HPLC" as purification.
    $> python cadnano_agg_order.py mydesign.staples.csv --scale 20nmU --purification HPLC

    # Read oligos from mydesign.staples.csv, output order file with header:
    # Sequence,Name,Design,Purification,Scale
    $> python cadnano_agg_order.py mydesign.staples.csv --header "Sequence Name Design Purification Scale" outsep=","

    # Read oligos from staples.csv, output order file where "Name" takes format of "rss045 TR-new":
    $> python cadnano_agg_order.py staples.csv --constant Design TR --namefmt "rss{idx:03d} {Design}-new" --idxstart 45


    $> cadnano_agg_order -y *.staples.csv --idxstart 74
        --header "Design Start Length Color Name Sequence Scale Purification"
        -r Design CircFoldback_0 CirFBv -r Design "braced" "b" --namefmt "rss{idx:03d} {Design}:" --outputsep ","

Default IDT scales and purification:
Code	Scale
25nm	25 nmole        (default for oligos)
100nm	100 nmole
250nm	250 nmole
1um	1 µmole
5um	5 µmole
10um	10 µmole
4nmU	4 nmole Ultramer™ (default for ultramers)
20nmU	20 nmole Ultramer™
PU	PAGE Ultramer™
25nmS	25 nmole Sameday


Code	Purification
STD	Standard Desalting
PAGE	PAGE $50.00
HPLC	HPLC $45.00
IEHPLC	IE HPLC $45.00
RNASE	RNase Free HPLC $75.00
DUALHPLC	Dual HPLC $80.00
PAGEHPLC	Dual PAGE & HPLC $130.00


"""


import os
import argparse
import glob
from datetime import datetime
#import json
#import yaml
#from collections import OrderedDict

verbose = 1


def read_oligos(filepath, sep=","):
    """ Return a list of dicts. """
    with open(filepath) as fp:
        lines = (line.strip() for line in fp if line[0] != "#")
        header = next(lines).split(sep)
        rows = [dict(zip(header, line.split(sep))) for line in lines]
    if verbose >= 2:
        print("{} oligos loaded from file {}".format(len(rows), filepath))
    return rows, header


def get_oligos(oligofiles, sep=","):
    """
    Nested or flat data structure?
    """
    designs = ((os.path.splitext(os.path.basename(fn))[0].split(".stap")[0], fn) for fn in oligofiles)
    nested = [(design, read_oligos(fn, sep=sep)) for design, fn in designs]
    flat = []
    for design, (oligos, _) in nested:
        for row in oligos:
            row["Design"] = design
            flat.append(row)
    if verbose >= 2:
        print("{} oligos total loaded from files {}".format(len(flat), oligofiles))
        if verbose > 2:
            print("flat[0]:", flat[0])
    return flat, nested


def add_fields(oligos, namefmt=None, idxstart=1, constants=None, replace=None):
    """ Add fields to oligo rows. """
    for i, row in enumerate(oligos, idxstart):
        if constants:
            row.update(constants)
        if replace:
            for key, find, repl in replace:
                row[key] = row[key].replace(find, repl)
        if namefmt:
            row["Name"] = namefmt.format(idx=i, **row)


def eliminate_duplicates(oligos):
    """
    Oligos is a flat list of oligos.
    Returns
        flat, duplicates, seqs
    Where
        flat is a list of oligos where duplicate oligos has been removed,
        duplicates is a list of all oligos that were removed from the flat list, and
        seqs is a set of the unique oligo sequences.
    """
    seqs = set()
    flat = []
    duplicates = []
    for oligo in oligos:
        if oligo["Sequence"] not in seqs:
            seqs.add(oligo["Sequence"])
            flat.append(oligo)
        else:
            duplicates.append(oligo)
    if verbose >= 2:
        print("** Unique seqs:   {}\n** Unique oligos: {}\n** Duplicates:    {}"\
              .format(len(seqs), len(flat), len(duplicates)))
    return flat, duplicates, seqs


def check_seqs(oligos):
    """ Check that all sequences are OK. """
    for oligo in oligos:
        #if any(b for b in oligo["Sequence"] == "?")
        if "?" in oligo["Sequence"]:
            raise ValueError("Oligo {} sequence contains undefined bases ('?')".format(oligo))
        if not oligo["Sequence"]:
            raise ValueError("Oligo {} has empty sequence".format(oligo))


def write_oligos(oligos, filepath, append=False, header=None, include_header=True, sep="\t"):
    if header is True or header is None:
        header = sorted(oligos[0].keys())
    with open(filepath, 'a' if append else 'w') as fp:
        if include_header:
            fp.write(sep.join(header) + "\n")
        fp.write("\n".join(sep.join(row.get(field, "") for field in header)
                           for row in oligos))
    if verbose >= 1:
        print("{} oligos {} to file {}".format(len(oligos), "appended" if append else "written", filepath))


def ok_to_write_to_file(filepath, argsns):
    """ Assert whether it is OK to write to staples_outputfn """
    if argsns.overwrite or argsns.append or not os.path.exists(filepath):
        return True
    # os.path.exists(staples_outputfn) is True
    overwrite = input(filepath + " already exists. Overwrite? [Y/n]")
    if overwrite and overwrite.lower()[0] == "n":
        return False
    return True


def parse_args(argv=None):
    """
    Parse and post-process command line arguments.
    """
    parser = argparse.ArgumentParser(description="Aggregate cadnano staples/oligos script.")
    parser.add_argument("--verbose", "-v", action="count", help="Increase verbosity.")
    parser.add_argument("--overwrite", "-y", action="store_true",
                        help="Overwrite existing order file if they already exists. "
                        "(Default: Ask before overwriting)")
    parser.add_argument("--append", "-a", action="store_true",
                        help="Append to existing file (rather than overwrite).")
    parser.add_argument("--inputsep", default=",")
    parser.add_argument("--outputsep", default="\t")

    ## Headers:
    #  All headers should be capitalized for consistency.
    parser.add_argument("--header", default="Name Sequence Scale Purification")
    parser.add_argument("--idxstart", default=1, type=int)
    parser.add_argument("--namefmt", default="rss{idx:03d} {Design} {Start}",
                        help="How to create oligo/sequence name.")
    parser.add_argument("--scale", help="Add a constant scale to all order line entries.")
    parser.add_argument("--purification", help="Add a constant purification to all order line entries.")
    parser.add_argument("--constant", nargs=2, help="Add a constant purification to all order line entries.")

    parser.add_argument("--replace", "-r", nargs=3, action="append", metavar=("key", "find-str", "repl-str"),
                        help="Replace <find-str> in row[key] with <repl-str> for all rows "
                        "(can be specified multiple times).")
    # Consider making scale and purification selection a bit more versatile and flexible by having a
    # selection spec file...?

    # NOTE: Windows does not support wildcard expansion in the default command line prompt!
    parser.add_argument("oligofiles", nargs="+", metavar="oligofile.csv",
                        help="One or more oligos.csv file (.csv) read oligos/staples from (exported from cadnano).")
    parser.add_argument("--outputfn", "-o", default="{date:%Y%m%d}.order.csv",
                        help="The filename to output the order to. "
                        "The output filename can include python format specifiers, "
                        #"e.g. {Design}, {cadnano_fname} and {seqfile}. "
                        "Default is {date:%Y%m%d}.order.csv")
    ## Parse:
    argsns = parser.parse_args(argv)
    ## Post-processing:
    # Expand filename patterns (required on windoze).
    argsns.oligofiles = [fname for pattern in argsns.oligofiles for fname in glob.glob(pattern)]

    return parser, argsns



def main(argv=None):
    # parser, args-namespace:
    import sys
    print("sys.argv:", sys.argv)
    _, argsns = parse_args(argv)
    print("argsns.replace:", argsns.replace)
    global verbose
    verbose = argsns.verbose or 0
    if argsns.scale or argsns.purification or argsns.constant:
        constants = {key: value for key, value in argsns.constant} if argsns.constant else {}
        constants.update({"Scale": argsns.scale, "Purification": argsns.purification})
    else:
        constants = None
    # flat, nested
    print("Loading oligos from files:", argsns.oligofiles)
    flat, _ = get_oligos(argsns.oligofiles, sep=argsns.inputsep)
    # flat, duplicates, seqs
    flat, _, _ = eliminate_duplicates(flat)
    add_fields(flat, namefmt=argsns.namefmt, idxstart=argsns.idxstart,
               constants=constants, replace=argsns.replace)
    #try:
    check_seqs(flat)
    #except
    outputfile = argsns.outputfn.format(date=datetime.now())
    outputheader = argsns.header.split()
    # Need to add Scale and Purification ?

    if not ok_to_write_to_file(outputfile, argsns):
        return 1

    write_oligos(flat, outputfile, append=argsns.append,
                 header=outputheader, include_header=True, sep=argsns.outputsep)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2011 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on 20130413

@author: scholer

Used to generate a purchase order from a cadnano-based design list
"""

import csv
import glob
import os.path

def generate_orderfile(designfilename):

    with open(designfilename, 'rU') as designfile:
        design = dict()
        CsvDialect = csv.Sniffer().sniff(designfile.read(1024))
        CsvDialect.lineterminator = '\n'  # Override default line terminator as sniffer always reports \r\n (0x0D,0x0A) as the line terminator.
        designfile.seek(0)
        # Important lesson: You DictReader has several more arguments, so you must define dialect=<dialect> for it to work.
        setreader = csv.DictReader(designfile, dialect=CsvDialect)
        design["FileFields"] = setreader.fieldnames
        design["Dataset"] = [row for row in setreader if len(row)>0]

    orderfields = ["Name", "Sequence", "Length"]
    designgroup = designfilename.split(".")[0]

    try:
        # if os.file.isfile('design_order_name_format.txt'):
        with open('order_name_format.txt') as format_file:
            order_name_format = "\n"+format_file.readline().strip()
            print("order name format is: {0}".format(order_name_format))
    except IOError:
        order_name_format = "\n{designgroup}:{modulename}:{start}"

    orderfilename = designfilename+'.ordersheet'
    with open(orderfilename, 'wb') as orderfile:
#        for i,row in enumerate(design["Dataset"]):
#            print (i, row.keys())
        orderfile.write("\t".join(orderfields))
        orderfile.writelines(["\t".join([
                order_name_format.format(modulename=row["Modulename"], start=row["Start"], designgroup=designgroup),
                row["Sequence"],
                row["Length"] if int(row["Length"])==len(row["Sequence"]) else "designfile length is {0} but len(seq) is {1}".format(row["Length"],len(row["Sequence"]))
                ])
            for row in design["Dataset"]])
        print("\ngenerate_orderfile() : Order info written to file {}".format(orderfilename))


def generate_pos(maxrow='H',maxcol=12):
    maxrow = maxrow.upper()
    order_by_rows = False
    filename = "generic_positions.txt"
    with open(filename,"wb") as fp:
        if not order_by_rows:
            for row in range(ord('A'),ord(maxrow)+1):
                for col in range(1,maxcol+1):
                    fp.write("\n{0}{1}".format(chr(row),col))
        else:
            for col in range(1,maxcol+1):
                for row in range(ord('A'),ord(maxrow)+1):
                    fp.write("\n{0}{1}".format(chr(row),col))
        print("{0} : generic positions written to file: {1}".format("generate_pos()", filename))


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(description='This script is used to produce order sheets from cadnano design oligo lists.')
    argparser.add_argument('designfilename', nargs='?', help="Use this oligo list. If none is given, the first *.smmc.sorted file will be used." )
    args = argparser.parse_args()
    if args.designfilename is None:
        designfilename = glob.glob("*.smmc.sorted")[0]
    else:
        designfilename = args.designfilename
    generate_orderfile(designfilename)
    generate_pos()

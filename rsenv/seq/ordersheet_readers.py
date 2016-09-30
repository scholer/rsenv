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

"""

Functions for reading oligo order sheets.

"""


import os
import re
import sys
import argparse
import csv
from openpyxl import load_workbook





def read_gsheet_worksheet(headers=None):
    if headers is None:
        pass
    elif headers == "standard":
        headers = "Date	Vendor	OligoID	Sequence	Scale	Purification	Comments".split()


def read_gsheet_partial_text(content, headers=None, dialect=None, dictreader=True, trim_seqs=False):

    if isinstance(content, str):
        rows = content.split("\n")
    else:
        rows = content
        content = "\n".join(rows)  # maybe strip all rows to make sure they don't end with '\n'?
    if dialect is None:
        dialect = csv.Sniffer().sniff(content)

    if headers is None:
        if 'date' in str(rows[0][0]).lower():
            headers = rows[0]
            rows = rows[1:]
        else:
            headers = "Date	Vendor	OligoID	Sequence	Scale	Purification	Comments".split()
    if dictreader:
        csvreader = csv.DictReader(rows, dialect=dialect, fieldnames=headers)
        rows = list(csvreader)
        if trim_seqs:
            for row in rows:
                row['Sequence'] = row['Sequence'].replace(' ', '')
    else:
        csvreader = csv.reader(rows, dialect=dialect, fieldnames=headers)
        rows = list(csvreader)

    # return list of dicts (or lists if dictreader is False)
    return rows


def get_sequences_from_csv_ordersheet(filename, pure=True):
    with open(filename) as fd:
        rows = fd.read().split("\n")
    rows = read_gsheet_partial_text(rows, dictreader=True)
    seqs = [row["Sequence"] for row in rows]
    if pure:
        seqs = [sequence_pure(seq) for seq in seqs]
    return seqs


def sequence_wo_mods(seq, format="IDT"):
    """

    :param seq:
    Returns:
        sequence without modifications.
    """
    mods_pat = r'\/\w*\/'
    # replace all instances of pattern with '':
    return re.sub(mods_pat, '', seq)


def sequence_pure(seq):
    seq = seq.replace(" ", "").replace("-", "").replace("*", "")
    seq = sequence_wo_mods(seq)
    return seq


def test():

    test_data = [
        ("/5Phos/CGCAGA GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC",
         "CGCAGA GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC"),
        ("/5BiosG/CGCAGA GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC/3AmMO/",
         "CGCAGA GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC"),
        ("/5Phos/CGCAGA/iCy5/ GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC/3Phos/",
         "CGCAGA GAACCCTAACCTAAGAATTCTTATAGAGAAGGTTTACCCTATCTGAGTGAGTAGC ATAGGC"),
    ]
    for before, expected in test_data:
        try:
            assert sequence_wo_mods(before) == expected
        except AssertionError:
            print("sequence_wo_mods(before): '%s'" % (sequence_wo_mods(before),))
            print("expected:                 '%s'" % (expected,))


    if len(sys.argv) > 1:
        # sys.argv[0] is current script
        print(sys.argv)
        csvfile = sys.argv[1]
        print("\n".join(get_sequences_from_csv_ordersheet(csvfile)))


if __name__ == '__main__':
    # hint: In pycharm, write: test().main [TAB] to postfix complete
    test()

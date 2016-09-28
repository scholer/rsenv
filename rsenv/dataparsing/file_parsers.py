#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2014 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

Module for parsing data files.

"""

import csv

from .tabulated_data import tabdata_as_dictlist
from .textdata_util import gen_trimmed_lines


def trimmed_lines_from_file(filepath, commentchar='#', commentmidchar=None):
    """
    Reads all non-comment parts of non-empty lines from file <filepath>,
    and returns these as a list, closing the file after loading the lines.
    See textdata_util.gen_trimmed_lines doc for info on commenchar and commentmidchar.
    """
    with open(filepath) as fd:
        trimmed_lines = list(gen_trimmed_lines(fd, commentchar, commentmidchar))
    return trimmed_lines



def dictlist_from_tabdatafile(fd, headers=None, sep=None, stripcells=True):
    """
    Create dictlist based on tabulated content in file.
    """
    tabdata = gen_trimmed_lines(fd)
    return tabdata_as_dictlist(tabdata, headers=headers, sep=sep, stripcells=stripcells)


def gen_csv_data_with_sniffer(inputfilehandle, sep=None, lineterminator=None):
    """
    Takes an input filehandle and returns a generator
    with rows represented as dicts.
    """
    if lineterminator is None:
        lineterminator = '\n'
    if sep is None:
        # First do some sniffing (I expect input smmc file to have headers!)
        snif = csv.Sniffer()
        csvdialect = snif.sniff(inputfilehandle.read(2048)) # The read _must_ encompass a full first line.
        #alternatively, select the separator character that is mentioned the most in the first row:
    #                sep =  max([',','\t',';'], key=lambda x: myline.count(x))
        inputfilehandle.seek(0) # Reset file
    else:
        csvdialect = csv.excel()
    csvdialect.lineterminator = lineterminator # Ensure correct line terminator (\r\n is just silly...)

    # Then, extract dataset:
    setreader = csv.DictReader(inputfilehandle, dialect=csvdialect)
    # Import data
    # Note: Dataset is a list of dicts.
    return (row for row in setreader if len(row)>0)

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
Rename IDT order files...

"""
import os
import glob
import csv
## Logging:
import logging
logger = logging.getLogger(__name__)


def read_csvfile(inputfn):
    """
    Reads a standard one-rack-per-file csv data file.
    """
    with open(inputfn, 'rU') as fd:
        datastruct = gen_csv_data(fd, returntype='list') # Make sure to store as list before closing file.
    return datastruct


def gen_csv_data(inputfilehandle, returntype='generator'):
    """
    Takes an input filehandle and returns a generator
    with rows represented as dicts.
    """
    # First do some sniffing (I expect input smmc file to have headers!)
    snif = csv.Sniffer()
    csvdialect = snif.sniff(inputfilehandle.read(4048)) # The read _must_ encompass a full first line.
    csvdialect.lineterminator = '\n' # Ensure correct line terminator (\r\n is just silly...)
    inputfilehandle.seek(0) # Reset file
    # Then, extract dataset:
    setreader = csv.DictReader(inputfilehandle, dialect=csvdialect)
    # Import data
    # Note: Dataset is a list of dicts.
    if returntype == 'list':
        return [row for row in setreader if len(row)>0]
    elif returntype == 'csvreader':
        return setreader
    else:
        return (row for row in setreader if len(row)>0)



if __name__ == '__main__':

    logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=logfmt)


    #import argparse
    cwd = os.getcwd()

    csvfiles = glob.glob("*.csv")

    for fn in csvfiles:
        data = read_csvfile(fn)
        try:
            orderno = data[0]["Sales Order"]
        except IndexError as e:
            logger.error( "IndexError for file '%s', len(data)=%s, msg = %s", fn, len(data), e )
        newfn = "IDT_order_{}.csv".format(orderno)
        fps = [os.path.join(cwd, f) for f in (fn, newfn)]
        print "Renaming '{}' to '{}'".format(*fps)
        os.rename( *fps )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2012 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

This module contains various functions to read and write rackfile data.

"""
import os.path

## Logging:
import logging
logger = logging.getLogger(__name__)
#logging.getLogger("__main__").setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)

from rsenv.origami.oligomanager_lib.filedatalib.fileutils import gen_csv_data, gen_xls_data, writecsvdata
from rsenv.origami.oligomanager_lib.filedatalib.fileutils import findFieldByHint



def read_rackfile(inputfn):
    """
    Reads a standard one-rack-per-file csv data file.
    """
    #with open(inputfn, 'rU') as filepath:
    #    #datastruct = gen_csv_data(filepath)
    #    return gen_csv_data(filepath)
    #return datastruct
    # Edit: Any of the above will produce an exception: "ValueError: I/O operation on closed file".
    with open(inputfn, 'rU') as fd:
        datastruct = list(gen_csv_data(fd)) # Make sure to store as list before closing file.
    return datastruct



def read_monolithic_rackfile(inputfn):
    """
    Takes an large monolithic input file with rackdata for many racks.
    Read the file and parse into data structure:
    dict(rackname=[list of dicts])
    each dict in the list of dicts corresponds to a row.
    """
    with open(inputfn, 'rU') as rackfilemulti:
        datastruct = read_rackfilehandle(rackfilemulti)
    return datastruct


def read_rackfilehandle(inputfh):
    """
    Takes an large monolithic input file with rackdata for many racks.
    Read the file and parse into data structure:
    dict(rackname=[list of dicts])
    each dict in the list of dicts corresponds to a row.
    """
    if hasattr(inputfh, 'name') and os.path.splitext(inputfh.name)[1] in ('.xls', '.xlsx'):
        csvdata = gen_xls_data(inputfh)
    else:
        csvdata = gen_csv_data(inputfh)
    racksdata = dict()
    racknamefield = None
    firstrow = next(csvdata)
    racknamefield = findFieldByHint(firstrow.keys(), ('plate name', 'rack name', 'rack', 'plate') )
    logger.info("Using racknamefield: %s", racknamefield)
    racksdata.setdefault(firstrow[racknamefield], list()).append(firstrow)
    for row in csvdata:
        racksdata.setdefault(row[racknamefield], list()).append(row)
    return racksdata


def filter_racksdata(racksdata, outputfields=None):
    """
    Takes a racksdata struct dict[rackname] = [list of row dicts]
    and removes undesired rows and does some value formatting,
    e.g. strips sequences.
    Usecase: You have a spec-sheet from manufacturer where the sequences
    have spaces for every 5 nucleotides.
    """
    # TODO: Consolidate with the rackfilter method from Oligomanager
    if outputfields is None:
        outputfields = ('Pos', 'Name', 'Sequence', 'nmoles')
    fieldhints = dict(pos = ('pos', 'position', 'well position', 'well'),
                      name = ('sequence name', 'oligo name', 'name'),
                      sequence = ('sequence', 'seq'),
                      nmoles = ('nmoles', 'nm'),
                      um = ('uM', u'Measured Concentration µM', u'µM')
                     )
    fieldsmap = None
    for rackdata in racksdata.values():
        for row in rackdata:
            if fieldsmap is None:
                fieldsmap = { field : findFieldByHint(row.keys(), hints) for field, hints in fieldhints.items() }
                logger.info("fieldsmap: %s", fieldsmap)
            row[fieldsmap['sequence']] = row[fieldsmap['sequence']].strip().replace(' ', '')
            if outputfields != 'all':
                for field in outputfields:
                    row[field] = row[fieldsmap[field.lower()]]
                popfields = set(row.keys()) - set(outputfields)
                for field in popfields:
                    del row[field]
    return racksdata


def write_rackdata(filehandle, rackdata, sortby=None, dialect=None):
    """
    Sorts rackdata and writes to filehandle.
    """
    rackdata = list(rackdata) # make sure to convert to list.
    firstrow = rackdata[0]
    if sortby is None:
        sortby = findFieldByHint(firstrow.keys(), ('pos', 'Position', 'well position') )
    if sortby:
        rackdata = sorted(rackdata, key = lambda x: x[sortby])
    writecsvdata(filehandle, rackdata, dialect)


def writerackdatastructstofiles(racksdata, outputfn_fmt='{rackname}_{index:02}.rack.csv', dialect=None):
    """
    Writes a multi-rack data structure to files, one file per rack.
    Inputs:
    racksstructs = dict[rackname] = [list of row dicts]
    """
    for i,(rackname, rackdata) in enumerate(sorted(racksdata.items()), 1):
        with open(outputfn_fmt.format(rackname=rackname, index=i), 'wb') as fh:
            write_rackdata(fh, rackdata, dialect=dialect)

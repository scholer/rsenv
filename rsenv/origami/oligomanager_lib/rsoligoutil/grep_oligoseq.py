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
#pylint: disable-msg=W0621,C0111

"""
Rapidly grep (search) through csv and xls(x) files and locate an oligo sequence.

Usage examples:
    grep_oligoseq.py AATTGCCCGT ~/oligo-sequences

"""
import os
import sys
ppath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

#print "__file__: {}".format(__file__)
#print "insert path: {}".format(ppath)
sys.path.insert(0, ppath)
#print sys.path
#sys.exit()
#import glob
import fnmatch
import csv
## Logging:
import logging
logger = logging.getLogger(__name__)
from xlrd.biffh import XLRDError


from rsenv.origami.oligomanager_lib.filedatalib.csvfileutils import gen_csv_data, findFieldByHint
from rsenv.origami.oligomanager_lib.filedatalib.xlsutils import gen_xls_data



def seqs_gen(datagen, fp=None):
    """
    Takes an input datatset generator.
    Locates a field like "sequence", "oligo sequence", "seq" or similar.
    Outputs all sequences as:
    (sequence, row) tuples.
    """
    rowidx = 1
    try:
        firstrow = next(datagen)
    except csv.Error as e:
        logger.error("csv.Error encountered while reading first row [ABORTING] [filepath: %s] [ERROR msg: %s]",
                     fp, e)
        raise StopIteration
    seqfield = findFieldByHint(list(firstrow.keys()), ("oligo sequence", "sequence", "seq", "oligo") )
    namefield = findFieldByHint(list(firstrow.keys()),
                                ("oligo name", "oligo_name", "sequence name", "order name", "name"),
                                scorebar=0.7, require="name")
    if seqfield is None:
        yield (",".join(list(firstrow.values())), rowidx, None)
        for rowidx, data in enumerate(datagen, rowidx+1):
            yield (",".join(str(v) for v in list(data.values())), rowidx, None)
    else:
        logger.debug("Using seqfield: %s", seqfield)
        yield (firstrow[seqfield].strip().replace(' ', ''), rowidx, firstrow[namefield] if namefield else None)
        for rowidx, data in enumerate(datagen, rowidx+1):
            if data[seqfield]:
                yield (data[seqfield].strip().replace(' ', ''), rowidx, data[namefield] if namefield else None)


def read_filedata(inputfh):
    """
    Takes an large monolithic input file with rackdata for many racks.
    Read the file and parse into data structure:
    dict(rackname=[list of dicts])
    each dict in the list of dicts corresponds to a row.
    """
    if hasattr(inputfh, 'name') and os.path.splitext(inputfh.name)[1] in ('.xls', '.xlsx'):
        try:
            csvdata = gen_xls_data(inputfh)
        except XLRDError as e:
            logger.error("XLRDError reading file %s, '%s', (NOT trying csv)...", inputfh, e)
            #try:
            #    csvdata = gen_csv_data(inputfh)
            #except csv.Error as e:
            #    logger.error("csv.Error reading file %s, '%s', skipping...", inputfh, e)
            return (i for i in tuple())
    else:
        csvdata = gen_csv_data(inputfh)
    return csvdata




def print_matching(matching, fn, args):
    """
    Prints matching.
    """
    if args.reportall:
        print("File {}: {} matches{}".format(fn, len(matching), ":" if matching else "."))
        print("\n".join("> line {:4} :  {}   \t   {}".format(row, seq, name)
                        for (seq, row, name) in matching ))
    elif matching:
        print("\n".join("{}:{} :  {}   \t   {}".format(fn, row, seq, name)
                        for (seq, row, name) in matching ))



def isbinary(fp):
    return any( fnmatch.fnmatch(fp, ext) for ext in ('*.xls', '.xlsx') )




if __name__ == '__main__':

    import argparse


    desc = r"""
OligoGrepper - grep oligo sequence in csv files.
Note: If you just want to grep text files and avoid spaces in sequences,
it might be easier/faster to do either of the following:
1) grep -nIR -E "A\s?G\s? ... (inserting "\s?" between all nucleotides in sequence)
1) Use "find <dir> -print0 | xargs <filter>" ...?
2) With python, just read file and remove all spaces.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--includepat', default="*.csv,*.xls,*.xlsx",
                        help="Process files matching these patterns (comma-separated text list).")
    parser.add_argument('sequence', help="Start processing from this dir.")
    parser.add_argument('basedir', nargs='?', help="Start processing from this dir.")
    parser.add_argument('--debug', action='store_true',
                        help="Enable debug logging. If nothing is specified, will enable debug logging for all modules.")
    parser.add_argument('--reportall', action='store_true', help="Print info for all files, even files with zero matching lines.")
    #parser.add_argument('--reportall', action='store_true', help="Print info for all files, even files with zero matching lines.")


    argsns = parser.parse_args()



    logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.DEBUG if argsns.debug else logging.INFO, format=logfmt)
    #if argsns.debug is None:
    #    #and 'all' in argsns.debug:
    #    logging.basicConfig(level=logging.INFO, format=logfmt)
    #    logger.debug("Log-level set to INFO.")
    ## argsns.debug is a list (possibly empty)
    #elif argsns.debug:
    ## argsns.debug is a non-empty list
    #    logging.basicConfig(level=logging.INFO, format=logfmt)
    #    for mod in argsns.debug:
    #        logger.info("Enabling logging debug messages for module: %s", mod)
    #        logging.getLogger(mod).setLevel(logging.DEBUG)
    #else:
    #    # argsns.debug is an empty list, debug ALL modules:
    #    logging.basicConfig(level=logging.DEBUG, format=logfmt)
    #    logger.debug("Log-level set to DEBUG.")




    if argsns.basedir is None:
        #argsns.basedir = os.getcwd()
        argsns.basedir = '.' # Better reporting, otherwise you get abs dir.
    fnpats = argsns.includepat.split(',')

    seqpat = "*{}*".format(argsns.sequence.lower())

    def fnmatcher(seq):
        #logger.debug("Comparing sequence '%s' against search pattern '%s'", seq, seqpat)
        return fnmatch.fnmatch(seq.lower(), seqpat)

    seqmatcher = fnmatcher


    def get_matching(filepath):
        with open(filepath, 'rb' if isbinary(filepath) else 'rU') as fd:
            matching = [ (seq, row, name) for (seq, row, name)
                            in seqs_gen(read_filedata(fd), fp=filepath)
                            if seqmatcher(seq) ]
        return matching


    if os.path.isfile(argsns.basedir):
        fp = argsns.basedir
        matching = get_matching(fp)
        print_matching(matching, fp, argsns)


    for root, dirs, files in os.walk(argsns.basedir):
        files = (fn for fn in files if fn[0] != '.')
        for fn in ( f for pat in fnpats for f in fnmatch.filter(files, pat) ):
            fp = os.path.join(root, fn)
            logger.debug("Parsing file: %s", fp)
            matching = get_matching(fp)
            print_matching(matching, os.path.join(root, fn), argsns)

    logger.debug("DONE!")

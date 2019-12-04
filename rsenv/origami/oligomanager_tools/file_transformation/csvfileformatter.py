#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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
# pylint: disable-msg=W0621
"""

Simple module to convert/format csv files:
- Change end-of-line (EOL) markers
- Change delimiter
- Strip spaces from data columns
(adding more functions as-needed)

"""


import os.path
import argparse
import logging
logging.addLevelName(4, 'SPAM')
logger = logging.getLogger(__name__)



def convertfiles(args):
    """
    Performs the file conversion.
    """
    for fn in args.files:
        fnroot, ext = os.path.splitext(fn)
        outputfn = args.outfnfmt.format(fnroot=fnroot, ext=ext)
        with open(outputfn, 'wb') as fout:
            with open(fn, 'rU') as fin:
                headerln = fin.readline()
                inputdelim = guessdelim(headerln)
                outputdelim = args.delimiter or inputdelim
                fieldheaders = headerln.strip().split(inputdelim)
                logger.debug("inputdelim='%s', outputdelim='%s', fieldheaders='%s', removespacesfromcol=%s, eolmarker=%s",
                             inputdelim.encode('string-escape'), outputdelim.encode('string-escape'),
                             fieldheaders, args.removespacesfromcol, args.eolmarker.encode('string-escape'))
                fout.write(outputdelim.join(fieldheaders)+args.eolmarker)
                for line in fin:
                    fields = line.strip().split(inputdelim)
                    if args.removespacesfromcol:
                        for i in args.removespacesfromcol:
                            fields[i] = fields[i].replace(' ', '')
                    out = outputdelim.join(fields)
                    fout.write(out+args.eolmarker)
        print "{} reformatted and written to file: {}".format(fn, outputfn)


def guessdelim(line, default=','):
    """ Guess delimiter (primitive) """
    candidates = ('\t', ',', ';')
    inline = (cand for cand in candidates if cand in line)
    return next(inline, default)


if __name__ == '__main__':
    logfmt = "%(levelname)s %(name)s:%(lineno)s %(funcName)s() > %(message)s"


    parser = argparse.ArgumentParser(description="Takes a csv file and converts the file and removes spaces from specified columns.")


    parser.add_argument('-e', '--eolmarker', default='\n',
                        help="End-of-line character to use. Default is '\\n'")
    parser.add_argument('-d', '--delimiter', default=',',
                        help="Column delimiter character to use. Detault is to use same delimiter as input file. ")
    parser.add_argument('-r', '--removespacesfromcol', metavar='<list of column indices>',
                        help="Remove spaces from these columns (except the header).\
Input multiple columns with -r 0,2,4,5 (separating indices with comma, NOT space).")
    parser.add_argument('-f', '--outfnfmt', default='{fnroot}-formatted{ext}',
                        help="Output file formatting. Note that extension *includes* the dot delimiter.")

    parser.add_argument('files', nargs='+', help="Input files to convert.")


    parser.add_argument('--debug', action='store_true', help="Print debug messages.")


    argsns = parser.parse_args() # produces a namespace, not a dict.

    # Adjust input args:
    if argsns.removespacesfromcol:
        argsns.removespacesfromcol = [int(i) for i in argsns.removespacesfromcol.split(',') ]
    argsns.delimiter = argsns.delimiter.decode('string-escape')
    argsns.eolmarker = argsns.eolmarker.decode('string-escape')

    loglevel = logging.DEBUG if argsns.debug else logging.INFO

    logging.basicConfig(level=loglevel, format=logfmt)

    convertfiles(argsns)

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

Note: This code implements two paradigms/idioms:
1) Functional. No unnessecary objects.

This is a helper script, aimed to solve the following scenario:
    You have a specsheet from IDT which includes oligos for multiple racks.
    The epmotion_staplemixer assumes one-file-per-plate.

Solution:
    1) Find a *.allracks.csv file or take one as first command line argument
    2) Read the file and parse into data structure:
        dict(rackname=[list of dicts])
        each dict in the list of dicts corresponds to a row.
    3) Write the information to a file.

Implementation:


"""

import glob
import sys
import os

## Logging:
import logging
logger = logging.getLogger(__name__)

# This directory might be subject to change...
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(scriptdir)
sys.path.append(os.path.dirname(scriptdir))
sys.path.append(os.path.dirname(os.path.dirname(scriptdir)))
logger.debug("sys.path is: %s", sys.path)
# The module might also change...
from rsenv.origami.oligomanager_lib.oligodatalib.rackfileutils import read_monolithic_rackfile, writerackdatastructstofiles, filter_racksdata


def find_default_inputfilename():
    """
    Return default file.
    """
    fn_cands = glob.glob('*.allracks.csv')
    if fn_cands:
        logger.info("file candidates found (returning the first in the list): %s", fn_cands)
        return fn_cands[0]





if __name__ == '__main__':

    logging.getLogger("__main__").setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("epmotion_staplemixer.epmotion_staplemixer").setLevel(logging.DEBUG)
    logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=logfmt)


    import argparse
    parser = argparse.ArgumentParser(description="""
This is a helper script, aimed to solve the following scenario:
    You have a specsheet from IDT which includes oligos for multiple racks.
    The epmotion_staplemixer assumes one-file-per-plate.
""" )
    #parser.add_argument('-f', '--designfilename', help="The exported cadnano sequence list, comma-separated file (*.csv).")
    # default is dictated by gen_input_filenames().
    parser.add_argument('-i', '--inputfile', help="Specify the large rackfile that is\
                        to be split into files with one rack per file.")
    parser.add_argument('--outputfn_fmt', default='{rackname}_{index:02}.rack.csv',
                        help="Output file format. Defaults to '{rackname}_{index:02}.rack.csv'")


    argsns = parser.parse_args() # produces a namespace, not a dict.

    inputfn = argsns.inputfile
    if not inputfn:
        inputfn = find_default_inputfilename()

    racksdata = read_monolithic_rackfile(inputfn)
    racksdata = filter_racksdata(racksdata)
    writerackdatastructstofiles(racksdata, argsns.outputfn_fmt)

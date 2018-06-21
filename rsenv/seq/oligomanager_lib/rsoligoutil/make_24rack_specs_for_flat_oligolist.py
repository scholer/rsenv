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
2) Memory efficient, always using generators rather than list.

This is a helper script, aimed to solve the following scenario:
- You have a lot of individual tubes that you want to re-suspend using the robot.

Solution:
1) List all oligos from manufacturer in a flat list, with a field 'nmoles'.
2) Input the list to this program.
3) Use the output *.rack.csv files as regular rack files for the main staplemixer script using --resuspend_only argument.

Implementation:
- Implemented as a series of generators :-)
1) Read/open the csv file.
2) For each entry, calculate pos from index.
3) At index 23, increase plate-index and reset tube index.
   - Alternatively, just use modulus and floor division.
4) For each plate (index), write to file tube_rack_{i}.rack.csv

Sprint evaluation:
1)  Doing the whole "multiple input files" added unneeded overhead.
2)  Using generators made testing a bit more tricky.
3)  Insisting on the pull-from-default ability also added a bit of overhead.
4)  Test-driven development worked well, althrough functional isolation also added
    some overhead (i.e. instead of just opening a file for writing, I had to create
    one separate functions that worked on a file(-like) object and another that
    would open the files.
5)  I missed having globally-available things.

Changes:
20131206: I realized that having an implicit pull-based setup where each generator
    in the generator chain can obtain a default value by pulling from the next generator
    in the chain does not work well with functional programming.
    Mostly because the dependencies are easily broken when the code is refactored.
    Thus, I now set up the chain explicitly in the if __name__ == '__main__'
    driver and push arguments explicitly.

"""

#import os
#import csv
from itertools import izip_longest


## Logging:
import logging
logger = logging.getLogger(__name__)

from rspyutilslib.oligodatalib.plateutils import indexToPos
from rspyutilslib.filedatalib.fileutils import gen_input_filehandles, gen_csv_datasets, writecsvdatasetstofiles



inputfiles = None


def gen_input_filenames():
    """
    Generator.
    Returns a generator with input file names
    """
    _input = inputfiles or ( 'flat_oligo_list.csv', )
    return (fn for fn in _input)


def gen_calculated_resuspend_data(csv_data, conc=100, plate_format='24'):
    """
    Generator.
    Arguments:
     - csv_data: iterable of row dicts
     - conc:     the concentration in uM used to calculate 'final_vol_ul'.
    Takes a csv_data generator, and for each row calculates:
    1) 'final_vol_ul'
    2) Plate position.
    """
    plate_formats = {'24': dict(ncols=6, nrowmax=4),
                     '96': dict(ncols=12, nrowmax=8)}
    to_pos_params = plate_formats[plate_format]
    # Note: This approach modified row in-place.
    # However, since the rows in csv_data are probably read-once generated values anyways
    # this shouldn't be problematic...:
    for i, row in enumerate(csv_data):
        if not row:
            continue
        row['final_vol_ul'] = float(row['nmoles'])/conc*1000 # V=n/c, n=100, c=100, but nmol/uM = ml, so multiply with 1000 to get ul.
        if 'Pos' in row:
            logger.warning("row #%s already contains field 'Pos', overwriting...")
        row['Pos'] = indexToPos(i, **to_pos_params)
        yield row
    # Alternative, avoiding a for loop, but cannot emit logger warnings:
    #return (
    #    dict(row,
    #         final_vol_ul=float(row['nmoles'])/conc*1000),
    #         row['Pos'] = indexToPos(i)
    #        )



def gen_calculated_resuspend_datasets(datasets, conc=100, plate_format='24'):
    """
    Convenience method,
    returns list-generator of datasets,
    using default settings.
    Uh, wait... you cannot just use a default generated input dataset and write that.
    You need to split each dataset into chunks.
    Note that this will also flatten the data!
    i.e. (long_dataset1, long_dataset2) --> (short_dataset1, short_dataset2, short_dataset3, short_dataset4, short_dataset5)
    """
    maxsize = int(plate_format)
    return (gen_calculated_resuspend_data(data, conc, plate_format) for dataset in datasets for data in split_data(dataset, maxsize))


def split_data(dataset, maxsize=24, generator_input=False):
    """
    Takes a single dataset and splits it into multiple datasets of length maxsize.
    This function is here mostly as a reference on how this can be acomplished
    as a one-liner statement.
    Arguments:
    - dataset: The dataset to split; must be iterable (e.g. a list or generator).
    - maxsize: Split dataset into subdatasets with this number of elements.
    - generator_input: Whether the input is a generator. If the dataset is not a generator,
      this should be set to false. If it is a generator, setting this will prevent an
      extra generator to be created.
    Note:
    This function uses izip_longest( *[generator]*maxsize ), which is really fast and
    works for most generator-like inputs. Some generator-like inputs, however,
    are does not behave sufficiently "object"-like, including xrange iterators (python2.7).
    This is because [xrange(10)]*2 = [xrange(10), xrange(10)], where the two xrange elements
    are *different iterators*!
    For all cases where the input is not sufficiently "generator-like", you should set
    generator_input to false.
    E.g., for maxsize=2:
     - izip_longest( *[xrange(6)]*2 ) -> (0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)
     - izip_longest( *[(i for i in xrange(6))]*2 ) -> (0, 1), (2, 3), (4, 5)
    Also note that izip_longest will use a default value to complete the last zip, i.e.:
         izip_longest(*[(i for i in xrange(8))]*3) -> (0, 1, 2), (3, 4, 5), (6, 7, None)
    """
    if not generator_input:
        # if dataset is a generator, this should still be the exact same as above,
        # so this is arguably the safer default:
        return izip_longest(*[(row for row in dataset)]*maxsize)
    else:
        # Optimization, but probably not worth it; generating new generators
        # should be a really fast and light-weight operation...
        # >>> %timeit [i for i in izip_longest(*[(i for i in rangegen(100))]*2) ]
        # 100000 loops, best of 3: 19.6 us per loop
        # >>> %timeit [i for i in izip_longest(*[rangegen(100)]*2) ]
        # 100000 loops, best of 3: 12 us per loop
        # (However, increasing 100 to 10000 means that adding an outer generator
        # makes the code run 50 percent slower!)
        return izip_longest(*[dataset]*maxsize)



if __name__ == '__main__':
    """
    You can implement one of two scenarios:
    1)  A pull-based implementation: You invoke the top-level generator, and that pulls default data from the lower-level generators,
        e.g.:
            gen_calculated_resuspend_datasets()
            |-> pulls from gen_csv_datasets()
                |-> gen_csv_datasets pulls filehandles from gen_input_filehandles and creates dataset for each filehandle with gen_csv_data
                    |-> gen_input_filehandles pulls from gen_input_filenames()
    2)  A push-based implementation:
        1) Get or define the filenames
        2) Get filehandle generator
        3) get csv_datasets generator.
    3) For a single, this simplifies to:
    """
    logging.getLogger("__main__").setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logging.getLogger("staplemixer.staplemixer").setLevel(logging.DEBUG)
    logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s\n"
    logging.basicConfig(level=logging.INFO, format=logfmt)



    import argparse
    parser = argparse.ArgumentParser(description="""
Generate 24 rack format files from a flat oligo list
""" )
    #parser.add_argument('-f', '--designfilename', help="The exported cadnano sequence list, comma-separated file (*.csv).")
    # default is dictated by gen_input_filenames().
    parser.add_argument('-i', '--inputfiles', nargs='*', help="Specify which oligolist files to use. \
                        If not specified, all files ending with *.oligolist.csv will be used. This arguments will \
                        take all following arguments, and can thus safely be used as --inputfiles *.list.txt")

    argsns = parser.parse_args() # produces a namespace, not a dict.


    inputfiles = argsns.inputfiles
    if not inputfiles:
        inputfiles = list(gen_input_filenames())

    inputfilehandles = gen_input_filehandles(inputfiles)
    csvdatasets = gen_csv_datasets(inputfilehandles)

    # old version passed input files implicitly. That is not a good practice with functional programming,
    # since functions may be relocated to a new module.
    resuspend_output_data = gen_calculated_resuspend_datasets(csvdatasets)
    writecsvdatasetstofiles(resuspend_output_data, outputfn_fmt='output_24wp_{:02}.rack.csv')

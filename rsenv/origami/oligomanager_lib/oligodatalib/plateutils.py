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
Contains various functions used to e.g. convert plate indices to string positions, etc.

"""


def posToRowColTup(pos):
    """
    Convert a alphanumeric position "A02" to row-column tuple (1,2),
    using 1-BASED INDEXING (!)
    e.g.:
        posToRowColTup('A01') => returns (1,1)
    Is used to convert src-plate positions.
    # ROW in German is Zeile, Column is Saule
    # epMotion index starts at 1, i.e. A1 is Z=1, S=1; A2 <=> Z=1, S=2, etc.
    """
    rownum = ord(pos[0].lower())-ord('a')+1 # "B04" should give a rownum of 2.
    colnum = int(pos[1:]) # "B04" should give rownum of 4;
    return rownum, colnum


def indexToRowColTup(index, ncols=12, nrowmax=8):
    """ Convert a linear index integer to row-column tuple, e.g. 8 -> (1,2)
        Is used to convert src-plate positions.
        # ROW in German is Zeile, Column is Saule
        # epMotion index starts at 1, i.e. A1 is Z=1, S=1; A2 <=> Z=1, S=2, etc.
        E.g.:
            indexToRowColTup(0) -> returns (1,1)
            indexToRowColTup(1) -> returns (1,2)
            indexToRowColTup(11) -> returns (1,12)
            indexToRowColTup(12) -> returns (2,1)
            indexToRowColTup(23) -> returns (2,12)
    """
    # destindex is defined by "for destindex, moduletopipet in enumerate(modulestopipet):"
    # index = 0 should return (1,1), index = 1 return (1,2), index 11 return (1,12), index 12 return (2,1).
    index = int(index)  # Doing cast is ok, but adding or subtracting anything just causes confusion.
    col = (index % ncols) + 1  # Watch out for modulus, returns from 0 to N-1.
    row = (index // ncols) + 1  # NOTE: Python 2 specific. Use floor (math module) for python3
    if row > nrowmax:
        print(f"indexToRowColTup() WARNING > index {index} with ncols={ncols}, nrowmax={nrowmax} "
              f"will return a row of {row}, exceeding the limit!")
    return row, col


def indexToPos(index, ncols=12, nrowmax=8):
    """
    Takes a (zero-based) index and converts it to a plate position,
    using ncols and nrowmax as plate layout, which defaults to
    ncols=12 and nrowmax=8.
    Is implemented using indexToRowColTup to convert index to row- and column index,
    which this method then converts to a string-based position.
    E.g.:
    - indexToPos(0)     => Returns 'A1'
    - indexToPos(11)    => Returns 'A12'
    - indexToPos(12)    => Returns 'B1'
    - indexToPos(11, ncols=6)    => Returns 'B6'
    - indexToPos(12, ncols=6)    => Returns 'C1'
    """
    row, col = indexToRowColTup(index, ncols, nrowmax)
    pos = "{0}{1:02}".format(chr(ord('A')+row-1), col)
    return pos

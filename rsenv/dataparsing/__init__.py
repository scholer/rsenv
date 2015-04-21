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


def file_as_(inputfn):
    """
    Reads a standard one-rack-per-file csv data file.
    """
    #with open(inputfn, 'rU') as filepath:
    #    #datastruct = gen_csv_data(filepath)
    #    return gen_csv_data(filepath)
    #return datastruct
    # Edit: Any of the above will produce an exception: "ValueError: I/O operation on closed file".
    with open(inputfn, 'rU') as filepath:
        datastruct = list(gen_csv_data(filepath)) # Make sure to store as list before closing file.
    return datastruct

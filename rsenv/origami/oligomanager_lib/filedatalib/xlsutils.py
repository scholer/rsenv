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
# pylint: disable-msg=W0612,R0903
"""

Module for extracting data from excel files.

"""


## Logging:
import logging
logger = logging.getLogger(__name__)


def gen_xls_data(fd):
    """
    Similar to gen_csv_data but produced from an excel file.
    Returns a generator of dicts.
    Read into memory before fd is closed.
    """
    # xlrd supports both old xls and new xlsx files :)
    from xlrd import open_workbook
    from mmap import mmap, ACCESS_READ
    #fmmap = mmap(f.fileno(),0,access=ACCESS_READ)
    logger.debug("Generating data for file: %s :: %s", fd.fileno(), fd.name)
    ### THIS ONLY WORKS FOR XLS FILES:::: #####
    wb = open_workbook( file_contents=mmap(fd.fileno(), 0, access=ACCESS_READ) )
    ws = wb.sheets()[0]
    logger.debug("Using worksheet: '%s'", ws.name)
    fieldheaders = ws.row_values(0)
    data = ( dict(list(zip(fieldheaders, ws.row_values(i)))) for i in range(1, ws.nrows) )
    return data

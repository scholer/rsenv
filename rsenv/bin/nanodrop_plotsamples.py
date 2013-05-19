#!/usr/bin/env python





"""
This will plot a single set of nanodrop data from a single file.
If the datafile is not given, None will the passed, which invokes 
file selector and sample selector as needed.
"""

import rsenv.rsplot.nanodropplotter as ndplotter
import sys

datafile = sys.argv[1] if len(sys.argv) > 1 else None
if len(sys.argv) < 3:
    selectedsamples = None
else:
    selectedsamples = sys.argv[2:]
    if len(selectedsamples) < 2:
        selectedsamples = selectedsamples[0].split(',')


ndplotter.plot_measurement(datafile, selectedsamples)

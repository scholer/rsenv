#!/usr/bin/env python

import rsenv
import sys

datafile = sys.argv[1] if len(sys.argv) > 1 else None
if len(sys.argv) < 3:
    selectedsamples = None
else:
    selectedsamples = sys.argv[2:]
    if len(selectedsamples) < 2:
        selectedsamples = selectedsamples[0].split(',')


rsenv.rsplot.rsnanodrop.plot_measurement(datafile, selectedsamples)

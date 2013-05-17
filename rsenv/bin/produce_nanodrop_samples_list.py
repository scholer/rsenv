#!/usr/bin/env python

import rsenv
import sys


filelist = sys.argv[1:]
#datafile = sys.argv[1] if len(sys.argv) > 1 else None
#samplename = sys.argv[2] if len(sys.argv) > 2 else None


rsenv.rsplot.rsnanodrop.produce_samplelist_for_files(printformat="{filename}:{sampleindex} {samplename}", filelist=filelist)

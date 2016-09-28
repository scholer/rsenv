# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 09:18:06 2013

Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com

@author: scholer
"""

import numpy as np # use as np.arange(...)
from matplotlib import pyplot # use as pyplot.scatter(...)
import operator
from collections import OrderedDict
import random

#
#
# class DataLoader():
#     def __init__():
#         self.Prefs = dict()
#
#
# def readCpDatafile(cpdatafile, qpcr_no_signal_cp_value=40):
#     with open(cpdatafile) as f:
#         cp_metadata = f.readline()
#         cpheader = f.readline().strip().split('\t')
#         # edit: instead of having a list of lists, I change so I have a list of dicts.
#         cpdata = [dict(zip(cpheader, line.strip().split('\t'))) for line in f if line.strip()[0] != "#"]
#     # cast all cp data to float:
#     for entry in cpdata:
#         try:
#             # for some reason using entry.get("Cp", qpcr_no_signal_cp_value)) yielded all empty Cp fields
#             entry["Cp"] = float(entry["Cp"]) if entry["Cp"] else qpcr_no_signal_cp_value
#         except ValueError, e:
#             print e
#             print "entry: {}, cp: '{}'".format(entry, entry.get("Cp", qpcr_no_signal_cp_value))
#
#     return cpdata, cp_metadata

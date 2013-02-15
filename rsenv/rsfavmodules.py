#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2011 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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
Created on Mon Apr  4 12:00:06 2011

@author: scholer

Imports my favorite modules that makes it possible for me to work efficiently 
with a python command prompt. It should never be loaded automatically, as loading 
takes quite some time.

Load this module with: from rsfavmods import *

"""


""" ---------------------------------
--- Modules from standard library ---
-------------------------------------
"""
# http://docs.python.org/2/library/

import os
import sys # has sys.argv, etc.
import math
import re
import string
import datetime
import random
import glob # glob.glob(path_pattern) returns list of files matching a certain glob pattern.
import pickle
import json
# import email, xmlrpclib, 
# import tkinter, IDLE, curses, 
## Clipboard in GTK:
import pygtk 
pygtk.require('2.0')
import gtk # gtk provides clipboard access:
# clipboard = gtk.clipboard_get()
# text = clipboard.wait_for_text()

""" ----------------------------------------
--- Modules outside the standard library ---
--------------------------------------------
"""

try:
    import yaml
except ImportError:
    print "YAML module not available."

try:
    import psycopg2
except ImportError:
    print "psycopg2 module not available"

try:
    import numpy
    try:
        import scipy
    except ImportError:
        print "scipy module not available."
    try:
        import Bio as biopython #http://biopython.org/DIST/docs/tutorial/Tutorial.html
    except ImportError:
        print "biopython ('Bio') module not available."
except ImportError:
    print "numpy module not available."
    print " - this also means no biopython, scipy, etc."




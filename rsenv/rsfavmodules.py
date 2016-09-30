#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2011 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Mon Apr  4 12:00:06 2011

@author: scholer

Imports my favorite modules that makes it possible for me to work efficiently
with a python command prompt. It should never be loaded automatically, as loading
takes quite some time.

Load this module with: from rsfavmods import *

Alternatively, just use this file as reference when you cannot remember what a particular
module is named.

"""


""" ---------------------------------
--- Modules from standard library ---
-------------------------------------
"""
# http://docs.python.org/2/library/

import os       # Has os.path, os.getcwd(), etc.
import sys      # has sys.argv, etc.
import math     # has math.pi and other mathematical constants and functions.
import re       # Regular expressions
import itertools # Fast iteration routines.
import string   # String functions
import datetime # datatime functions
import random   # Making random numbers, etc.
import glob     # glob.glob(path_pattern) returns list of files matching a certain glob pattern.
import pickle   # For persisting of objects and other python data
import json     # Persisting data in javascript object notation format
# yaml         # Persisting in Yet Anoter Markup Language. Is imported via try-except statement.
#import psycopg2# Connection to postgresql database. Is imported via try-except statement.
# numpy         # Imported via try-except statement
# scipy         # Imported via try-except statement




# import email      # For sending emails via python. See also smtplib, poplib and imaplib
# import xmlrpclib  # Remote procedure call library
# import curses     # Primitive command-line semi-GUI.
# import tkinter    # Python interface to Tcl/tk primitive GUI (http://docs.python.org/2/library/tk.html)
#                   #   used for e.g. the IDLE python code editor.
# For other GUIs, see http://docs.python.org/2/library/othergui.html



# --------------------------------------------
# --- Modules outside the standard library ---
# --------------------------------------------

## Clipboard in GTK:
try:
    import pygtk
    pygtk.require('2.0')
    import gtk # gtk provides clipboard access:
    # clipboard = gtk.clipboard_get()
    # text = clipboard.wait_for_text()
except ImportError:
    # Will happen on Windows/Mac:
    pygtk = None
    gtk = None


try:
    import yaml
except ImportError:
    print("YAML module not available.")
    yaml = None


# Postgres SQL driver:
try:
    import psycopg2
except ImportError:
    print("psycopg2 module not available")
    psycopg2 = None

# Scientific modules:
try:
    import numpy
    try:
        import scipy
    except ImportError:
        print("scipy module not available.")
except ImportError:
    print("numpy module not available.")
    print(" - this also means no biopython, scipy, etc.")
    numpy = None
    scipy = None

# Biopython, for DNA/Protein stuff:
try:
    import Bio
    import Bio as biopython  # http://biopython.org/DIST/docs/tutorial/Tutorial.html
except ImportError:
    print("biopython ('Bio') module not available.")
    Bio = None
    biopython = None


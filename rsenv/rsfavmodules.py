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
with a python command prompt.

This should be imported as:
from rsfavmods import *
Alternatively, if you do not want to import large modules 
such as os, sys, psycopg2, datetime, pygtk, etc
but only need your own stuff,
then you can just go ahead and import rsenv/__init__.py (import the dir).

See also:
 - https://docs.google.com/document/d/10bSiPwq4DrLGoB8zaCJBG3nrtK5-nC21Yhx-cCEyCO4/edit
 - Dropbox/Dev/Projects/OligoManager2/oligomanager
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools
 - Dropbox/Dev/Projects/OligoManager2/python_scripts  (obsolete)
 - Dropbox/NATlab shared/DesignBlueprints/caDNAno/A-few-hints-for-using-python.txt
 - Dropbox/Dev/Python/Python-copy-paste-examples.txt

Other tips for a better interpreter:
 - See env/__init__.py
 - http://rc98.net/pystartup

Also consider:
 - Using the ipython interpreter as your default interactive interpreter.
"""





import psycopg2
import os, sys
# import blast, ?

## Clipboard in GTK:
import pygtk # 
#pygtk.require('2.0')
import gtk
# clipboard = gtk.clipboard_get()
# text = clipboard.wait_for_text()



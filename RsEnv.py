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
"""


import psycopg2
import os, sys
import env # in this way, I can call with env.<something>.
#from env import * # My own custom modules, e.g. RsConfluence, RsSeqManip
# import blast, ?

## Clipboard in GTK:
import pygtk # 
#pygtk.require('2.0')
import gtk
clipboard = gtk.clipboard_get()

class RsHelper(object):
    def __init__(self):
        self.helpItems = dict() # Add to this.
        self.helpTopic = '' # Current help topic
        self.helpTopicsOrder = list()

    def printHelp(self, topic=None):
        # Ahh, max on a list returns the last item.
        maxlength = max([len(i) for i in self.helpTopicsOrder])
        ndecorators = 3
        for topic in self.helpTopicsOrder:
            print "\n"
            print "-"*(maxlength+2*(ndecorators+1))
            print " ".join(["-"*ndecorators, topic.center(maxlength), "-"*ndecorators])
            print "-"*(maxlength+2*(ndecorators+1))
            print 
            print "\n".join(self.helpItems[topic])
    
    def settopic(self, topic):
        self.helpTopic = topic
        if topic not in self.helpItems:
            self.helpItems[topic] = list()
        if topic not in self.helpTopicsOrder:
            self.helpTopicsOrder.append(topic)

    def addhelp(self, txt):
        self.helpItems[self.helpTopic].append(txt)

h = RsHelper()
def addhelp(txt):
    h.addhelp(txt)
def settopic(txt):
    h.settopic(txt)
def printHelp():
    h.printHelp()

settopic("Using this py-glet:")
addhelp("""In this module I keep all the python stuff I use regularly. This includes
both frequently used 'external' modules and my own hand-written stuff. In this way I
won't have to manually import everything when I run a python console, but can simply 
write import RsEnv

Use with either of the following: 
  - import RsEnv [as rs]
  - import * from RsEnv

With the first you need to prepend everything with e.g. "rs", but it does make it
easier to e.g. do rs = reload(rs)

Extension modules to RsEnv:
 - env.RsDatabase: ?
 - env.RsOligo: Imports modules usable for dealing with oligos. Also tries connects to oligomanager database.
 - env.RsLogic: Own handwritten functions.
 - env.RsLegacy: Handwritten legacy code.
 
 
 Automatically imported with this module:
  - Clipboard logic from pygtk+gtk
  - Psycopg2 database adaptor (postgres)
  - Scipy and Numpy

If this module was imported with import RsEnv as rs, you must call e.g. 
psycopg2 with rs.psycopg2


(asterix indicates that this is automatically loaded when importing this module)
""")

settopic("Basic file ops")
addhelp("file = open(<str filename>, <mode=['rb','wb',etc]>)")

settopic("Clipboard")
addhelp("Clipboard (with pygtk and GTK on Linux):")
addhelp("Copy to clipboard: clipboard.set_text(text)")
addhelp(" -- use clipboard.store() to make available to other apps.")
addhelp("Get text from clipboard: clipboard.set_text(text)")
addhelp("Alternatives for linux: Tkinter, xsel, xclip")
addhelp("Alternatives for windows: Try google ;-)")

def copyToClipBoard(txt):
    """ Illustrates how to use the clip-board """
    clipboard.set_text(txt)

settopic("Psycopg2")
addhelp("""The following has already been created for you (if you entered a db password):
 - conn = psycopg2.connect("host=10.14.40.243 user=postgres database=oligomanager password=<pass>")
 - cur = conn.cursor()
Cursor usage:
 cur.execute(sql, <param tuple>)  -- using %s in the sql as param placeholder.
 cur.executemany(operation, seq_of_params) # can be used for e.g. adding multiple rows.
 row1 = cur.fetchone(), or:
 dataset = cur.fetchall()
 use cur.mogrify(...) to see a print of the sql.
 cur.rowcount # Number of rows in cursor
 
Persisting:
 conn.commit(), or conn.rollback()
 cur.close()  (implicit rollback)
 conn.close()
Copy from file to table, or copy to file from table.
 cur.copy_from(<from_file>,<str to_table>,sep='\t',null='\N',columns=None)
 cur.copy_to(<to_file>, <str from_table>, ...)
 cur.copy_expert(sql, file, [size-of-file-buffer])
""")


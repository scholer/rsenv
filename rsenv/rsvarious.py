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
Created on Fri Feb 8 2013

@author: scholer

Includes various general-purpose python code

"""


import gtk # Used to access clipboard

def clipboard():
    print "Clipboard content: gtk.clipboard_get().wait_for_text()"
    print " - Also: wait_for_image(), etc. Set with set_text(...)"
    ret = gtk.clipboard_get().wait_for_text()
    print ret
    return ret

def cbget():
    print "Clipboard content: gtk.clipboard_get().wait_for_text()"
    return gtk.clipboard_get().wait_for_text()

def cbset(txt):
    gtk.clipboard_get().set_text(txt)


"""
-------------
-- Various --
-------------

RGBconv

Converting from hex to dec: int('number-as-string', <base>), e.g. int('33', 16) 
"""
def hextodec(num):
    return int(num, 16)

"""
Converting from dec to hex: hex(<decimal number'), e.g. hex(55)
 - or alternatively using string formatting (returns a string): "%x" % <dec number>, e.g. "%x" % 254
 - This is well-suited for caDNAno, e.g. color = "#%02X%02X%02X" % (10, 16, 253)
 - For more info see http://docs.python.org/library/string.html#format-specification-mini-language
Just for reference, this is what is should be: """
def dectohex(num):
    return hex(num)

""" Convert rgb tuple to color string """
def rgbconv(color):
  if isinstance(color, tuple):
    # Certainly a RGB colorÉ
    print "hel"
    


""" Convert a *decimal* color tuple to hex-based color string"""
def rgbdectohex(color):
  # color as tuple
  return "#"+''.join([str(hex(color[0])), str(hex(color[1])), str(hex(color[2]))])

""" Convert a hex-based color string to decimal color tuple """
def rgbhextodec(color):
  # color as string
  if color[0] == '#':
    color = color[1:]
  return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def combinationsexclude(elems, r=2, excludepairs=set(), doprint=True, returnstr=False, rsdebug=True):
    """ 
    Do combinatorics (default=binary) and filter the list to exclude certain pairs.
    E.g. you want to create all possible combinations of the numbers 1,2,3,4,5,6
    but you do not want to include combinations of: (1 and 2) or (3 and 5) or (4 and 6).
    I.e. you want: (1, 3), (1, 4), (1, 5), (1, 6), (2, 3), (2, 4), (2, 5), (2, 6), (3, 4), (3, 6), (4, 5), (5, 6)
    Use this method like: combinationsexclude(range(1,6), [(1,2),(3,5),(4,6)])
    Edit: Can now be run with r > 2, e.g. 
        rsenv.bincombexclude(range(1,5),[(2,1,3)],r=3)
    returns [(1, 2, 4), (1, 3, 4), (2, 3, 4)]
    Can easily be run as a copy/paste friendly oneliner as seen. See refs to augment to your needs.
    Refs:
     - http://docs.python.org/2/library/itertools.html
     - http://docs.python.org/2/library/sets.html
    """
    if isinstance(elems,int):
        elems = range(elems)
    excludepairs = set(excludepairs) # Make sure we have a set of tuples and not just a list of tuples.
    import itertools
    def isok(tup):
        return not (tup in excludepairs or reversed(tup) in excludepairs)
    #F = [tup for tup in itertools.combinations(range(1,7),2) if isok(tup)]
    # This is only guaranteed to work if r <= 2.(It might work, not certain)
    #F = [tup for tup in itertools.combinations(elems,r) if not (tup in excludepairs or reversed(tup) in excludepairs)]
    # If r > 2, I have to check whether any permutation of the tuple is among the excluded pairs list:
    H = [tup for tup in itertools.combinations(elems,r) if not set(itertools.permutations(tup)).intersection(excludepairs)] 
#    set1.intersection(set2) shorthand: set1 & set2
    # filter-based alternative. I generally find the list-comprehension-with-condition easier to read.
    #G = filter(lambda tup: not (set(itertools.permutations(tup)).intersection(excludepairs)), itertools.combinations(elems,r))
    s="\n".join([" ".join([str(i) for i in tup]) for tup in H])
    if doprint:
        print s
    if returnstr:
        return s
    return H



"""
====================
-- Email related ---
====================

Given string: a = “””
Steffen Sparvath <steffensparvath@gmail.com>,
 Denis Selnihhin <deonyz@hotmail.com>,
 Rasmus Schøler Sørensen <scholer@inano.au.dk>,
 Anders Okholm <andersokholm@me.com>,
 Hans Christian Høiberg <hchoeiberg@gmail.com>,
 Mathias Vinther <Mvinther@gmail.com>”””

", ".join([b.split("<")[1][0:-1] for b in a.split(",")])       produces
'steffensparvath@gmail.com, deonyz@hotmail.com, scholer@inano.au.dk, andersokholm@me.com, hchoeiberg@gmail.com, Mvinther@gmail.com'
"""
def getEmailAddFromString(a, returntype="string"):
    if returntype == "string":
        return ", ".join([b.split("<")[1][0:-1] for b in a.split(",")])



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


""" Convert a *decimal* color tuple to hex-based color string"""
def rgbdectohex(color):
  # color as tuple
  return ''.join(str(hex(color[0]), str(hex(color[1]), str(hex(color[2])) 

""" Convert a hex-based color string to decimal color tuple """
def rgbhextodec(color):
  # color as string
  if color[0] == '#':
    color = color[1:]
  return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


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
    if returntype = "string":
        return ", ".join([b.split("<")[1][0:-1] for b in a.split(",")])



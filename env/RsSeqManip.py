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

Includes various python code that I use frequently for manipulating DNA sequences.
"""


def DNAstrip(a):
    """ Easy stripping of all characters except ATGC. """
    return ''.join([x for x in a.upper() if x in 'ATGC'])
    """
Here is another alternative using build-in filter function and lambda expression:
b = filter(lambda x: x in 'ATGC', a)
lambda functions are a short-hand way to write simple, anonymous functions. Many similar use-cases, e.g.: map(lambda x: x**3, (1,2,3))
Albeit anonymous, references to lambdas can be assigned like such: l = lambda x: x**3
    """


""" Add space for every 8th base:"""
def DNAformat(a):
    b = DNAstrip(a)
    return ''.join([(letter+' ' if i % 8 == 7 else letter) for i,letter in enumerate(b)]).strip()


""" Complementary sequence """
def DNAcomplement(a):
    return ''.join([{"t":"a","a":"t","c":"g","g":"c"}[x] for x in a.lower()])[::-1]   #([start:end:slice])
    # Alternatively, brug af map function i stedet for for loop)
    b = "".join(map(lambda x: {"t":"a","a":"t","c":"g","g":"c"}[x], a.lower())[::-1])


""" 
----------------------
--- CADNANO stuff ----
----------------------
"""




""" Parsing, handling and manipulating set file information """

def appendSequence





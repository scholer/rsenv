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

Includes various python code that I use frequently for proteins
"""

"""
-------------------------------------
-- Protein/amino acid calculations --
-------------------------------------


--------- Protein charge --------------
# http://njms2.umdnj.edu/biochweb/education/bioweb/PreK2010/AminoAcids.htm
"""
def aacharge(aa, pH=7):
  if len(aa) > 1: 
    print "aa should only be one aminoacid. Use proteincharge for sequences..."
    return None
  aa = aa.lower()
  nonpolar="avliopmfw"
  polar="gstcnqy" # histidine only +0.1
  anionic="de"
  cationic="kr"
  if (aa in nonpolar) or (aa in polar): return 0
  if aa in anionic: return -1
  if aa in cationic: return 1
  if aa is "h": return 0.1
  return None

"""
Specific count, e.g. lysine and arginines:
aacount = len([aa for aa in protseq if aa in "kr"])
"""
def aacount(protseq, aatocount):
    return len([aa for aa in protseq if aa in aatocount])


class AminoAcidProp():
    def __init__(self):
        aa="avliopmfwgstcnqyh de kr h"
        aachargemap = {"a":0,"v":0,"l":0,"i":0,"o":0,"p":0,"m":0,"f":0,"w":0,"g":0,"s":0,"t":0,"c":0,"n":0,"q":0,"y":0,"d":-1,"e":-1,"k":1,"r":1,"h":0.1}

    def protcharge(self, protseq):
        # protseq=<aa seq>
        aachargemap = self.aachargemap
        return sum([aachargemap[aa] for aa in protseq.lower() if aa in aachargemap])

    def protchargealt(protseq):
        return aacharge(protseq)


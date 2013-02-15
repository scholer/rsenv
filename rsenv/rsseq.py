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
Created on Fri Feb 8 2013

@author: scholer

Includes various python code that I use frequently for manipulating DNA sequences.
"""


def dnastrip(a):
    """ Easy stripping of all characters except ATGC. """
    print "return ''.join([x for x in a.upper() if x in 'ATGC'])"
    return ''.join([x for x in a.upper() if x in 'ATGC'])
    """
Here is another alternative using build-in filter function and lambda expression:
b = filter(lambda x: x in 'ATGC', a)
lambda functions are a short-hand way to write simple, anonymous functions. Many similar use-cases, e.g.: map(lambda x: x**3, (1,2,3))
Albeit anonymous, references to lambdas can be assigned like such: l = lambda x: x**3
    """


""" Add space for every 8th base:"""
def dnaformat(a):
    b = DNAstrip(a)
    return ''.join([(letter+' ' if i % 8 == 7 else letter) for i,letter in enumerate(b)]).strip()

""" Reverse sequence """
def reverse(a):
    print "return a[::-1]   #([start:end:slice])"
    return a[::-1]   #([start:end:slice])
    # Alternatively, brug af map function i stedet for for loop)
    b = "".join(map(lambda x: {"t":"a","a":"t","c":"g","g":"c"}[x], a.lower())[::-1])


""" Complementary sequence (reading 3to5 prime; useful for underlaying sequences) """
def dnacomplement_3to5p(a):
    return ''.join([{"t":"a","a":"t","c":"g","g":"c"}[x] for x in a.lower()])   #([start:end:slice])


""" Reverse complementary sequence """
def dnacomplement(a):
    return ''.join([{"t":"a","a":"t","c":"g","g":"c"}[x] for x in a.lower()])[::-1]   #([start:end:slice])
    # Alternatively, brug af map function i stedet for for loop)
    b = "".join(map(lambda x: {"t":"a","a":"t","c":"g","g":"c"}[x], a.lower())[::-1])



""" 
----------------------
--- CADNANO stuff ----
----------------------

See also:
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools/file_transformation

"""




""" Parsing, handling and manipulating set file information """

def appendSequenceToStaps(staplesetfilepath, appendSeq, filtercolor=None, fiveprime=False,
    isComplement=False, desc="", verbose=0, outsep='\t', writeToFile=True, appendToFile=False):
    """ Color will filter only staples with a particular color.
    Similar to 
    Dropbox/Dev/Projects/OligoManager2/oligomanager/tools/file_transformation/sequencemapper.py
    but more simple """
    if isComplement:
        appendSeq = dnacomplement(appendSeq).upper()
        print "Appending seq: " + appendSeq
    if writeToFile:
        if appendToFile: fileflags = 'a'
        else: fileflags = 'w'
        newfile = open(staplesetfilepath+'.append', fileflags)
    else:
        import stringio.StringIO as StringIO
        newfile = StringIO()
    with open(staplesetfilepath,'rb') as fp:
        testline = fp.readline().strip()
        sep = '\t' if (len(testline.split('\t')) > len(testline.split(','))) else ','
        if outsep is None: outsep = sep
        header = testline.split(sep)
        hm = dict([(v,i) for i,v in enumerate(header)])
        fp.seek(0)
        for line in fp:
            row = line.strip().split(sep)
            if len(row)>1 and row[hm['Color']] == filtercolor or filtercolor == None:
                seq = row[hm['Sequence']]
                Start = row[hm['Start']]
                if fiveprime:  seq = "".join([appendSeq, seq])
                else:       seq = "".join([seq, appendSeq])
                ln = "\t".join([desc+":"+Start, seq]) if desc else seq
                if verbose: print ln
                newfile.write(ln+"\n")
    newfile.close()



""" Testing """

if __name__ == "__main__":

    thomasseq =   "ACATACAGCCTCGCATGAGCCC"
    rcomplement = "GGGCTCATGCGAGGCTGTATGT"
    useseq =      "GGGCTCATGCGAGGCTGTATGTTT" # with a 2-T linker to minimize strain
    appendSequenceToStaps('TR.ZS.i-4T.set', useseq, filtercolor="#03b6a2", desc="TR:col02-ss", fiveprime=True)
    appendSequenceToStaps('TR.ZS.i-4T.set', useseq,   filtercolor="#1700de", desc="TR:col08-ss", 
                            fiveprime=True, appendToFile=True, isComplement=False)



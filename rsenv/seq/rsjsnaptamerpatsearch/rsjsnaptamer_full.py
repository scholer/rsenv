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
Created on Fri April 19 2013

@author: scholer

Includes various python code to search for patterns in aptamer sequences.
"""

from __future__ import print_function
import string
import re
import itertools
import json
import time

dnacomplementmap = string.maketrans('ACGTacgt ', 'TGCATGCA ')
def dnarcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)[::-1]
def dnacomp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)


# Defines searches and other constants
constseq1 = "GCTGTTA"
constseq = constseq1
const2_3p5p = "CCGTTT"
#constseq2 = dnarcomp(const2_3p5p)
constseq2 = const2_3p5p[::-1]
#seq1 = "ATTCGG"
#seq2 = "ATC"
bases = "ATGC"
search_string = "NNNNGCTGTTANNNN" # Optionally allow for in-betweeners?

#this_run_id = datetime.datetime.
this_run_id = time.strftime("%Y%m%d-%H%M%S")
print("RUN ID: {0}".format(this_run_id))

### LOAD SEQUENCE DATA ###
#seqdata = list(enumerate(seqdata)) # I want to be able to refer to the original line.
#with open("N35_BBB_seqdata.txt") as fh:
## Reading standard format
##    seqdata = parseseqfile(fh)
#    seqdata = [(seqid.strip(),seqstr.strip().upper()) for seqid,seqstr in itertools.izip_longest(*[fh]*2)]

with open("BION.BAR_C8.F.clean.FR.clean.uniq") as fh:
    #http://10.14.32.145:8001/JSN-Dec-2012/Results/BION.BAR_C8.F.clean.FR.clean.uniq
    #Reading uniq format.
    #@164886
    #TTTTTTTAGCACCGCTGTTAGAGTATACCCTTTGCCG
    #+seq_count=1
    #cchhfhiicdgggiihhgbefihfdecechiihffhf
    #    seqdata = parseseqfile(fh)
    # (idstring, seq) tuples
    seqdata = [("{atid}_{count}".format(atid=seqitem[0].strip(), count=seqitem[2].strip().split("=")[1]),
                seqitem[1].strip().upper()) for seqitem in itertools.zip_longest(*[fh]*4)]



## DO FAST INITIAL FILTERING OF SEQUENCE DATA ###
print("Seqdata items before first filtering: {0}".format(len(seqdata)))
seqdata = [seqstring for seqstring in seqdata if constseq1 in seqstring[1]]
print("Seqdata items after first filtering: {0}".format(len(seqdata)))
seqdata = [seqstring for seqstring in seqdata if constseq2 in seqstring[1]]
print("Seqdata items after second filtering: {0}".format(len(seqdata)))
if len(seqdata)<100:
    print("Seqdata:")
    print("\n".join([" > ".join(seqitem) for seqitem in seqdata]))
else:
    f = open("Seqdata_filtered.txt", 'wb')
    print("Seqdata:", file=f)
    print("\n".join([" > ".join(seqitem) for seqitem in seqdata]), file=f)

#for seq in filter(lambda seq: seq1 in seq, sequencedata):
#    if not seq2 in seq: 
#        continue
nmatch = 0
print("Total permutations to search: {0}".format(4**8))
outputpatterns = open("outputpatterns.txt", "wb")
results = open("N35_pat2_results"+this_run_id+".txt", "wb")

def makepat():
    # Various search pattern options, stored for later use.
    seqpat = "".join([part1, constseq, part2])
    # search only for NNNN.*?GCTGTTA.*?NNNN
    search_pat1 = ".*?".join([
        part1,
        constseq,
        part2])
    # Search for "NNNNGCTGTTANNNN.*?"+dnarcomp(NNNNGCTGTTANNNN)
    search_pat2 = ".*?".join([seqpat, dnarcomp(seqpat)])
    seqpat2 = dnarcomp(part2)+constseq2+dnarcomp(part1)
    search_pat3 = ".*?".join([seqpat, seqpat2])
    search_pat=search_pat3

resultsdata = list()

for b1 in bases:
    for b2 in bases:
        for b3 in bases:
            print("Searching for sequences in format of {}".format("".join([b1, b2, b3])+constseq1+"NNNN.*?NNNN"+constseq2+dnarcomp("".join([b1, b2, b3]))))
            for b4 in bases:
                part1="".join([b1, b2, b3, b4])
                #print("Searching for sequences in format of {}".format(part1+constseq+"NNNN.*?NNNN"+dnarcomp(part1+constseq)))
                #print("Searching for sequences in format of {}".format(part1+constseq1+"NNNN.*?NNNN"+constseq2+dnarcomp(part1)))
                for b12 in bases:
                    for b13 in bases:
                        for b14 in bases:
                            for b15 in bases:
                                part2="".join([b12, b13, b14, b15])
                                seqpat = "".join([part1, constseq, part2])
                                seqpat2 = dnarcomp(part2)+constseq2+dnarcomp(part1)
                                #seqpat2b = dnarcomp(part1+const2_3p5p+part2)
                                #seqpat2c = 
                                #if not seqpat2 == seqpat2b:
                                #    print("seqpat2 is not same as seqpat2b:\n{0}\n{1}".format(seqpat2,seqpat2b))
                                #    raise Exception
                                search_pat = ".*?".join([seqpat, seqpat2])
                                search_pat2 = ".*?".join([seqpat2, seqpat])
                                progs = [re.compile(pat) for pat in [search_pat, search_pat2]]
                                print([prog.pattern for prog in progs], file=outputpatterns)
                                #print search_pat
                                for i, seqstring in enumerate(seqdata):
                                    for prog in progs:
                                        match = prog.search(seqstring[1])
                                        if match:
                                            resultsdata.append((seqstring, 
                                                dict(inputfilelineno=i, 
                                                    matchgroup=match.group(), regexpat=match.re.pattern, 
                                                    matchspan=match.span(), matchstring=match.string,
                                                    nmatch=nmatch)
                                                              ))
                                            nmatch += 1
                                            print("{nmatch},{i}:{seqid} > {matchingpart}\n- matching regex: {pat}\n- full sequence: {strseq}\n- span: {span}".format(
                                                nmatch=nmatch, 
                                                i=i,
                                                seqid=seqstring[0], 
                                                matchingpart=match.group(),
                                                pat=match.re.pattern,
                                                strseq=match.string,
                                                span=match.span()
                                                ), file=results#, flush=True #flush only for python3
                                                )
                                            print("{nmatch},{i}:{seqid} > {matchingpart}\n- matching regex: {pat}\n- full sequence: {strseq}\n- span: {span}".format(
                                                nmatch=nmatch, 
                                                i=i,
                                                seqid=seqstring[0], 
                                                matchingpart=match.group(),
                                                pat=match.re.pattern,
                                                strseq=match.string,
                                                span=match.span()
                                                ))
results.close()
outputpatterns.close()
fh.close()
with open("N35_pat2_results_"+this_run_id+".json", 'wb') as f:
    print(resultsdata[0])
    json.dump(resultsdata, f)

# 10.14.32.145:8001  
# http://10.14.32.145:8001/JSN-Dec-2012/Results/

# Alternatively, use the for loop to generate a very long regex and run only that one regex 
# once against every line.

def parseseqfile(f):
#    seqdata = list()
#    while True
#        seqid = readline(fh)
#        seqstr = readline(fh)
#        if not seqstr: break # EOF
#        seqdata.append((seqid,seqstr))

# Alternative, also from http://stackoverflow.com/questions/1657299/how-do-i-read-two-lines-from-a-file-at-a-time-using-python
    import itertools
#    for lines in itertools.izip_longest(*[f]*2):
#        print lines
    # If it is a problem having an iterator on the open file, consider dropping the data to a list.
    seqdata = [(seqid, seqstr.upper()) for seqid, seqstr in itertools.zip_longest(*[f]*2)]


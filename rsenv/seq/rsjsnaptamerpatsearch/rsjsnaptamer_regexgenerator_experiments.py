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
import profile

# Defines searches and other constants
constseq1 = "GCTGTTA"
constseq = constseq1
const2_3p5p = "CCGTTT"
#constseq2 = dnarcomp(const2_3p5p)
constseq2 = const2_3p5p[::-1]
#seq1 = "ATTCGG"
#seq2 = "ATC"
bases = "ATGC"
#search_string = "NNNNGCTGTTANNNN" # Optionally allow for in-betweeners?





## UTIL FUNCTIONS:

dnacomplementmap = string.maketrans('ACGTacgt ', 'TGCATGCA ')
def dnarcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)[::-1]
def dnacomp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)

bc = dict(A="T", T="A", G="C", C="G")



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
    #seqdata = parseseqfile(fh) # This is for the other datatype
    # Note: this reverses the dataset, if you do not apply [::-1] or similar...
    # *[fh]*4 <-- 4 denotes the number of lines in a single "read element".
    seqdata = [("{atid}_{count}".format(atid=seqitem[0].strip(), count=seqitem[2].strip().split("=")[1]),
                seqitem[1].strip().upper()) for seqitem in itertools.zip_longest(*[fh]*4)]



## DO FAST INITIAL FILTERING OF SEQUENCE DATA ###
print("Seqdata items before first filtering: {0}".format(len(seqdata)))
seqdata = [seqstring for seqstring in seqdata if constseq1 in seqstring[1]]
print("Seqdata items after first filtering: {0}".format(len(seqdata)))
seqdata = [seqstring for seqstring in seqdata if constseq2 in seqstring[1]]
print("Seqdata items after second filtering: {0}".format(len(seqdata)))
if len(seqdata)<100 and False:
    print("Seqdata:")
    print("\n".join([" > ".join(seqitem) for seqitem in seqdata]))
else:
    with open("Seqdata_filtered.txt".format(this_run_id), 'wb') as f:
        print("Seqdata:", file=f)
        print("\n".join([" > ".join(seqitem) for seqitem in seqdata]), file=f)
    with open("Seqdata_filtered.csv", 'wb') as f:
        print("seqid,reads,sequence", file=f)
        print("\n".join([",".join(seqitem[0].split("_")+list(seqitem[1:])) for seqitem in seqdata]), file=f)
    reads = [int(seqitem[0].split("_")[1]) for seqitem in seqdata]
    print("Total sequences / reads : {0} / {1}".format(len(reads), sum(reads)))

#for seq in filter(lambda seq: seq1 in seq, sequencedata):
#    if not seq2 in seq: 
#        continue
nmatch = 0
print("Total permutations to search: {0}".format(4**8))



def findPatternB_with_generator4(infile=None):
    outputpatterns = open("outputpatternsB_generator4.txt", "wb")
    results = open("N35_pat2_results_2_generator4.txt", "wb")
    resultsdata = list()

#    hp4perms = ("".join([AGTC[i],AGTC[ii],AGTC[iii],AGTC[iv],".*",AGTC[iv-2],AGTC[iii-2],AGTC[ii-2],AGTC[i-2]])
#                    for i in range(4) for ii in range(4) for iii in range(4) for iv in range(4) )
    hp4perms = ["".join([s1a2, s1a3, s1a4, constseq1, s2a1, s2a2, s2a3, s2a4, ".*", bc[s2a4], bc[s2a3], bc[s2a2], bc[s2a1], constseq2, bc[s1a4], bc[s1a3], bc[s1a2]])
                    for s2a1 in bases for s2a2 in bases for s2a3 in bases for s2a4 in bases
                    for s1a2 in bases for s1a3 in bases for s1a4 in bases
                    ]
    stem2alternations = "|".join(hp4perms)

    seqgenhp4 = ("{stem1}({stem2}){stem1rc}".format(\
        constseq1=constseq1, constseq2=constseq2,
        stem1="".join([a1]), stem2=stem2alternations,
        stem1rc="".join([bc[a1]])) \
        for a1 in bases)# for a2 in bases)# for a3 in bases)# for a4 in bases)

    nmatch = 0
    for search_pat in seqgenhp4:
        prog = re.compile(search_pat)
        print(search_pat, file=outputpatterns)
#        continue
        for i, seqstring in enumerate(seqdata):
            match = prog.search(seqstring[1])
            #match = re.search(search_pat, seqstring[1])
            if match:
                resultsdata.append((seqstring, 
                    dict(inputfilelineno=i, 
                        matchgroup=match.group(), regexpat=match.re.pattern, 
                        matchspan=match.span(), matchstring=match.string,
                        nmatch=nmatch)
                                  ))
                nmatch += 1
                resdict = dict(
                    nmatch=nmatch, 
                    i=i,
                    seqid=seqstring[0], 
                    matchingpart=match.group(),
                    pat=match.re.pattern,
                    strseq=match.string,
                    span=match.span()
                )
                print("{nmatch},{i}:{seqid} > {matchingpart}\n- full sequence: {strseq}\n- span: {span}".format(
                    **resdict
                    ), file=results#, flush=True #flush only for python3
                    )
    results.close()
    outputpatterns.close()
    fh.close()
# end findPatternB_with_generator3


def findPatternB_with_generator3(infile=None):
    outputpatterns = open("outputpatternsB_generator3.txt", "wb")
    results = open("N35_pat2_results_2_generator3.txt", "wb")
    resultsdata = list()

#    hp4perms = ("".join([AGTC[i],AGTC[ii],AGTC[iii],AGTC[iv],".*",AGTC[iv-2],AGTC[iii-2],AGTC[ii-2],AGTC[i-2]])
#                    for i in range(4) for ii in range(4) for iii in range(4) for iv in range(4) )
    hp4perms = ["".join([constseq1, s2a1, s2a2, s2a3, s2a4, ".*", bc[s2a4], bc[s2a3], bc[s2a2], bc[s2a1], constseq2])
                    for s2a1 in bases for s2a2 in bases for s2a3 in bases for s2a4 in bases
#                    for s1a4 in bases
                    ]
    stem2alternations = "|".join(hp4perms)

    seqgenhp4 = ("{stem1}({stem2}){stem1rc}".format(\
        constseq1=constseq1, constseq2=constseq2,
        stem1="".join([a1, a2, a3, a4]), stem2=stem2alternations,
        stem1rc="".join([bc[a4], bc[a3], bc[a2], bc[a1]])) \
        for a1 in bases for a2 in bases for a3 in bases for a4 in bases)

    nmatch = 0
    for search_pat in seqgenhp4:
        prog = re.compile(search_pat)
        print(search_pat, file=outputpatterns)
#        continue
        for i, seqstring in enumerate(seqdata):
            match = prog.search(seqstring[1])
            #match = re.search(search_pat, seqstring[1])
            if match:
                resultsdata.append((seqstring, 
                    dict(inputfilelineno=i, 
                        matchgroup=match.group(), regexpat=match.re.pattern, 
                        matchspan=match.span(), matchstring=match.string,
                        nmatch=nmatch)
                                  ))
                nmatch += 1
                resdict = dict(
                    nmatch=nmatch, 
                    i=i,
                    seqid=seqstring[0], 
                    matchingpart=match.group(),
                    pat=match.re.pattern,
                    strseq=match.string,
                    span=match.span()
                )
                print("{nmatch},{i}:{seqid} > {matchingpart}\n- full sequence: {strseq}\n- span: {span}".format(
                    **resdict
                    ), file=results#, flush=True #flush only for python3
                    )
    results.close()
    outputpatterns.close()
    fh.close()
# end findPatternB_with_generator3

def findPatternB_with_generator2(infile=None):
    outputpatterns = open("outputpatternsB_generator2.txt", "wb")
    results = open("N35_pat2_results_2_generator2.txt", "wb")
    resultsdata = list()


    AGTC = "AGTC" # this makes it easy, a complement to bases[i] is always bases[i-2].
    hp4perms = ("".join([AGTC[i], AGTC[ii], AGTC[iii], AGTC[iv], ".*", AGTC[iv-2], AGTC[iii-2], AGTC[ii-2], AGTC[i-2]])
                    for i in range(4) for ii in range(4) for iii in range(4) for iv in range(4) )
#    seqgenhp4 = ["".join([a1,a2,a3,a4,".*",bc[a4],bc[a3],bc[a2],bc[a1] ])
#                    for a1 in bases for a2 in bases for a3 in bases for a4 in bases]
    stem2alternations = "|".join(hp4perms)

    seqgenhp4 = ("{stem1}{constseq1}({stem2}){constseq2}{stem1rc}".format(\
        constseq1=constseq1, constseq2=constseq2,
        stem1="".join([a1, a2, a3, a4]), stem2=stem2alternations,
        stem1rc="".join([bc[a4], bc[a3], bc[a2], bc[a1]])) \
        for a1 in bases for a2 in bases for a3 in bases for a4 in bases)

    nmatch = 0
    for search_pat in seqgenhp4:
        prog = re.compile(search_pat)
        print(search_pat, file=outputpatterns)
#        continue
        for i, seqstring in enumerate(seqdata):
            match = prog.search(seqstring[1])
            #match = re.search(search_pat, seqstring[1])
            if match:
                resultsdata.append((seqstring, 
                    dict(inputfilelineno=i, 
                        matchgroup=match.group(), regexpat=match.re.pattern, 
                        matchspan=match.span(), matchstring=match.string,
                        nmatch=nmatch)
                                  ))
                nmatch += 1
                resdict = dict(
                    nmatch=nmatch, 
                    i=i,
                    seqid=seqstring[0], 
                    matchingpart=match.group(),
                    pat=match.re.pattern,
                    strseq=match.string,
                    span=match.span()
                )
                print("{nmatch},{i}:{seqid} > {matchingpart}\n- full sequence: {strseq}\n- span: {span}".format(
                    **resdict
                    ), file=results#, flush=True #flush only for python3
                    )
    results.close()
    outputpatterns.close()
    fh.close()
# end findPatternB_with_generator


def findPatternB_with_generator(infile=None):
    outputpatterns = open("outputpatternsB_generator.txt", "wb")
    results = open("N35_pat2_results_2_generator1.txt", "wb")
    resultsdata = list()
    seqgenhp4 = ("{a1}{a2}{a3}{a4}.*?{b1}{b2}{b3}{b4}".format(a1=a1, a2=a2, a3=a3, a4=a4, b1=bc[a1], b2=bc[a2], b3=bc[a3], b4=bc[a4])
                for a1 in bases for a2 in bases for a3 in bases for a4 in bases)
    # optimization: insert constant stuff:
    regextemplate = "{part1}{constseq1}{part2}.*?{part1rc}{constseq2}{part2rc}".format(part1="{part1}",
        constseq1=constseq1, part2="{part2}", part1rc="{part1rc}", constseq2=constseq2, part2rc="{part2rc}")

    seqgenhp4 = ("{stem1}{constseq1}{stem2}.*?{stem2rc}{constseq2}{stem1rc}".format(\
        constseq1=constseq1, constseq2=constseq2,
        stem1="".join([a1, a2, a3, a4]), stem2="".join([b1, b2, b3, b4]),
        stem1rc="".join([bc[a4], bc[a3], bc[a2], bc[a1]]), stem2rc="".join([bc[b4], bc[b3], bc[b2], bc[b1]])) \
        for a1 in bases for a2 in bases for a3 in bases for a4 in bases \
        for b1 in bases for b2 in bases for b3 in bases for b4 in bases )
#    seqgenhp4m = ("{part1rc}{constseq2}{part2rc}.*?{part1}{constseq1}{part2}".format(\
#        constseq1=constseq1, constseq2=constseq2,
#        part1="".join([a1,a2,a3,a4]), part2="".join([b1,b2,b3,b4]),
#        part1rc="".join([bc[a1],bc[a2],bc[a3],bc[a4]]), part2rc="".join([bc[b1],bc[b2],bc[b3],bc[b4]][::-1])) \
#        for a1 in bases for a2 in bases for a3 in bases for a4 in bases \
#        for b1 in bases for b2 in bases for b3 in bases for b4 in bases )
    nmatch = 0
    for search_pat in seqgenhp4:
        prog = re.compile(search_pat)
        print(search_pat, file=outputpatterns)
#        continue
        for i, seqstring in enumerate(seqdata):
            match = prog.search(seqstring[1])
            #match = re.search(search_pat, seqstring[1])
            if match:
                resultsdata.append((seqstring, 
                    dict(inputfilelineno=i, 
                        matchgroup=match.group(), regexpat=match.re.pattern, 
                        matchspan=match.span(), matchstring=match.string,
                        nmatch=nmatch)
                                  ))
                nmatch += 1
                resdict = dict(
                    nmatch=nmatch, 
                    i=i,
                    seqid=seqstring[0], 
                    matchingpart=match.group(),
                    pat=match.re.pattern,
                    strseq=match.string,
                    span=match.span()
                )
                print("{nmatch},{i}:{seqid} > {matchingpart}\n- matching regex: {pat}\n- full sequence: {strseq}\n- span: {span}".format(
                    **resdict
                    ), file=results#, flush=True #flush only for python3
                    )
    results.close()
    outputpatterns.close()
    fh.close()
# end findPatternB_with_generator

def findPatternB_with_forLoops():
## Note: this actually searches for ((([constseq1](((((.*)))))[constseq2])))
#                                  b123           4 1315  (rest is given by the first part)
#                                                 b1214
    outputpatterns = open("outputpatterns.txt", "wb")
    results = open("N35_pat2_results_2_forloop.txt", "wb")
    #csvfile = open("N35_pat2_results_2"+this_run_id+".csv", "wb")
    #csvfile.write("nmatch,i,seqid,matchingpart,full_seq,matching_regex,span")
    resultsdata = list()
    nmatch = 0
    for b1 in bases:
        for b2 in bases:
            for b3 in bases:
                #print("Searching for sequences in format of {} (and other with hairpin on other side)".format("".join([b1,b2,b3,"("])+constseq1+"((((.*?))))"+constseq2+")"+dnarcomp("".join([b1,b2,b3]))))
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
                                    progs = [re.compile(pat) for pat in [search_pat]]#, search_pat2]]  ------ NOTE THIS IS COMMENTED OUT FOR DEBUGGING !! 
                                    #print([prog.pattern for prog in progs], file=outputpatterns)
                                    #print search_pat
                                    print(search_pat, file=outputpatterns)
#                                    continue
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
                                                resdict = dict(
                                                    nmatch=nmatch, 
                                                    i=i,
                                                    seqid=seqstring[0], 
                                                    matchingpart=match.group(),
                                                    pat=match.re.pattern,
                                                    strseq=match.string,
                                                    span=match.span()
                                                )
                                                print("{nmatch},{i}:{seqid} > {matchingpart}\n- matching regex: {pat}\n- full sequence: {strseq}\n- span: {span}".format(
                                                    **resdict), file=results)#, flush=True #flush only for python3
#                                                print("{nmatch},{i}:{seqid} > {matchingpart}\n- matching regex: {pat}\n- full sequence: {strseq}\n- span: {span}".format(
#                                                    **resdict))
                                                #csvfile.write("{nmatch},{i},{seqid},{matchingpart},{full_seq},{matching_regex},{span}".format(**resdict))
    results.close()
    outputpatterns.close()
    fh.close()
# end findPatternB_with_forLoops



#with open("N35_pat2_results_"+this_run_id+".json",'wb') as f:
#    print(resultsdata[0])
#    json.dump(resultsdata, f)


# def makepat():
#     """
#     Not used at this moment.
#     """
#     # Various search pattern options, stored for later use.
#     seqpat = "".join([part1, constseq, part2])
#     # search only for NNNN.*?GCTGTTA.*?NNNN
#     search_pat1 = ".*?".join([
#         part1,
#         constseq,
#         part2])
#     # Search for "NNNNGCTGTTANNNN.*?"+dnarcomp(NNNNGCTGTTANNNN)
#     search_pat2 = ".*?".join([seqpat, dnarcomp(seqpat)])
#     seqpat2 = dnarcomp(part2)+constseq2+dnarcomp(part1)
#     search_pat3 = ".*?".join([seqpat, seqpat2])
#     search_pat=search_pat3



# http://10.14.32.145:8001/JSN-Dec-2012/Results/

def parseseqfile(f):
    print("parseseqfile() !")
    seqdata = [(seqid, seqstr.upper()) for seqid, seqstr in itertools.zip_longest(*[f]*2)]


if __name__ == "__main__":
    """
To time execution within code:
    1) profile.run("command") within in the code (will slow down execution, so use only for inspection)
    2)  start_time = time.time()
        main()
        end_time = time.time()
        print "Execution time: {0} s".format(end_time-start_time)
    
to time execution from outside (i.e. from the command line):
    time python script.py
    python -mtimeit script.py
    
    OBSERVATIONS:
     - Using profile.run() increases runtime 10-30x (Probably cases like this with many for loops is not handled very well...?)
     - Generator is 0.2s slower than for loop? (At least the generator i made...). 
        ---> This is because I re-use a compiled regex prog instead of making them over and over. (changing that and they run exactly the same).
     - But, that is still running through 4**8 = 65e3 loops in 10 secs. So, _my_ code is not adding
       a lot of overhead. Thus, it is regex searching each and every line in the file that takes so long.
     - This also meeans that the "optimizations" in the iterator are moot. Again, this shows that there is rarely benefit
       of doing optimizations before you know they are really needed.
     - Doing 4**8 = 65e3 is not much compared to the total number of sequences (660e3). Hence, not surprising that this part
       is what takes the longest.
       
       Generator2 which compiles a regex with 4**4=256 (alter|nations) only takes 3.9 secs instead of 10 ! 
       (on the 256 line .partial file, which had 5 dataset entries after filtering)
       Increasing to 10000 lines (198 unique sequences after filter):
       generator2: 4.09 sec
       generator1: 17.3 sec
       forLoop:    18.9 sec

       Increasing to 100000 lines (2248 unique sequences after filter):
       generator2:   4.5 sec
       generator1: 102 sec
       forLoop:     89 sec

        However, simply increasing the regex expression much longer (i tried to extend the expression by *4 and got 16 secs instead of 4 secs.)
       
       Test, setting a "continue" in the for loop, thus not running any regex searches (but still doing regex prog compilation)
       With 10000 lines (198 unique sequences after filter):
       generator3: 16.3 sec
       generator2:  4.01 sec
       generator1: 10.8 sec
       forLoop:    10.5 sec

       Test, setting a "continue" BEFORE the for loop, thus not running any regex searches 
       (still doing regex prog compilation, but this time not going over the data entries)
       With 10000 lines (198 unique sequences after filter):
       generator3: 16.4 sec
       generator2:  3.95 sec
       generator1:  9.85 sec
       forLoop:     9.85 sec

        If I try to change the regex with alternations from generator2, moving the constseq regions inside,
        execution time goes from 4.0 to 7.2 secs without regex search (continue escape)
        (and same with regex search, on 10000 lines file, 200 seqs after filter.)
        For full file, this takes 9.4 secs for generator3 and 5.9 for generator2. So, about the same extra.
        

        If I continue this, as generator4, now moving the stem1 bases into the (alter|nation) part,
        for first extra base (s1a4), execution time goes from 9 to 11.8 secs (with regex search, on full 600k lines file, 13000 seqs after filter.)
        without search, time is:
        gen4: 7.18
        gen3: 7.02
        gen2: 4.03
        gen1: ---
        another base, s1a3 moved in:
        gen4: 28.0    (52.6 secs if I dont alleaviate by removing s1a3 from for loop)
        gen3: 9.17
        gen2: 6.22
        another base, s1a2 moved in:
        gen4: 195   
        gen3:   9.2
        gen2:   6.7
        
        The results clearly indicate that a long regex is preferred only up to a certain point,
        at least when using (alter|nations). 
        I was not able to produce a regex using conditional (?(if)then|else), 
        with the if asserting an named earlier named match. 
        See obsolete expressions at the end of this file for my attempts.
       
    """
    #profile.run("findPatternB_with_forLoops()")
    #profile.run("findPatternB_with_generator()")
    
    start_time = time.time()
    findPatternB_with_generator4()
    end_time = time.time()
    print("Execution time for generator4: {0} s".format(end_time-start_time))

    start_time = time.time()
    findPatternB_with_generator3()
    end_time = time.time()
    print("Execution time for generator3: {0} s".format(end_time-start_time))

    start_time = time.time()
    findPatternB_with_generator2()
    end_time = time.time()
    print("Execution time for generator2: {0} s".format(end_time-start_time))

    start_time = time.time()
    #findPatternB_with_generator()
    end_time = time.time()
    print("Execution time with generator1: {0} s".format(end_time-start_time))
    
    start_time = time.time()
    #findPatternB_with_forLoops()
    end_time = time.time()
    print("Execution time with forLoop: {0} s".format(end_time-start_time))
    # 



""" 
OBSOLETE.


Unfortunately, I cannot get this to work:

(?P<s1a1>[ATGC])(?P<s1a2>[ATGC])(?P<s1a3>[ATGC])(?P<s1a4>[ATGC])   # stem1, strand a
(?P<const1>GCTGTTA)
(?P<s2a1>[ATGC])(?P<s2a2>[ATGC])(?P<s2a3>[ATGC])(?P<s2a4>[ATGC])    # stem2, strand a
.*  # a loop
(?(?P<s2a4>=A)T|G)   # if s2a4 is an A, this must be T, else if it is G, this must be C, else (...)
(...)






a="{stem1}{constseq1}{stem2}.*?{stem2rc}{constseq2}{stem1rc}"
# s1 = "Stem #1", s1a = strand a, stem1. s1a1 = basepair1, strand a on stem1
a=r'(?P<s1a1>[ATGC])(?P<s1a1>[ATGC])(?P<s1a1>[ATGC])(?P<s1a1>[ATGC])GCTGTTA'
  r'(?<s1a1>=A


"TTTCCG"

(?P<s1a1>[ATGC])(?P<s1a2>[ATGC])(?P<s1a3>[ATGC])(?P<s1a4>[ATGC])    # stem1, strand a
(?P<const1>GCTGTTA)                                                 # const1
(?P<s2a1>[ATGC])(?P<s2a2>[ATGC])(?P<s2a3>[ATGC])(?P<s2a4>[ATGC])    # stem2, strand a
.*  # a loop
(?(?P<s2a4>=A)T|G)


Alternativt:

(AAAA.*TTTT|
#"{stem1}{constseq1}({}.*?{stem2rc}{constseq2}{stem1rc}".format(...alternation=



"""


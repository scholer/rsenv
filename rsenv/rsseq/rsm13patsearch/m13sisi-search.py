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
Created on 2013/06/07

@author: scholer

Includes various python code to search for patterns in the M13 sequence.
"""

#from __future__ import print_function
import string
import re
import itertools
#import json
#import time

from dnasequences import sequences

dnacomplementmap = string.maketrans('ACGTacgt ','TGCATGCA ')
def dnarcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)[::-1]
def dnacomp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)


class Myseq:
    def __init__(self, seq, seqis3p5p=None):

        self.Seqstr = seq
        self.Seq = list() # WC sequence; ATGC only.
        self.Annotation = list() # Annotates each nucleotide in seq.
        self.Seqsplit = list() # each item is a string.
        self.Seq, self.Annotation = self.parseSeq(seq)
        # This must be done at the end; otherwise the annotation prefixes will become post-fixes.
        if seqis3p5p:
            self.Seq = self.Seq[::-1]
            self.Annotation = self.Annotation[::-1]
    
    def parseSeq(self, seqstr):
        annotation = list()
        wcseq = list()
        wcnucs = "ATGC"
        previous_was_annotation = False
        for s in seqstr:
            if s in wcnucs:
                if not previous_was_annotation:
                    annotation.append('')
                wcseq.append(s)
                previous_was_annotation = False
            else:
                if previous_was_annotation:
                    raise ValueError("Double annotation not supported. {}".format([s,seqstr, wcseq, annotation]))
                previous_was_annotation = True
                annotation.append(s)
        return wcseq, annotation

    def __repr__(self):
        ret = self.Seqstr
        ret += '\n' + "\n".join([
            "".join([x if x else ' ' for x in item])
            for item in (self.Seq, self.Annotation)])
        return ret + '\n' + "".join(["{}{}".format(self.Annotation[i],nt) for i,nt in enumerate(self.Seq)])

antihandle_seq = "CAlCGTClTGTlTG"[::-1].replace("l","") # written in 3' to 5'; l prefix denotes LNA nucleotide.

ah_seq = Myseq("CAlCGTClTGTlTG", True)
print ah_seq

handle_seq = dnarcomp(antihandle_seq)

sisi_templ_seq = "ACUUGUGGC--CGUUUACGUClGlCU".replace("l","").replace("-","") # written 5' to 3';
sisi_compl_seq1 = "UlClTUGAAlCAlCCG"[::-1].replace("l","") # written in 3' to 5'; l prefix denotes LNA nucleotide.
sisi_compl_seq2 = "GlCAAAUGlCAG"[::-1].replace("l","") # written in 3' to 5'; l prefix denotes LNA nucleotide.

#print "Seqs:"
#print "\n".join([antihandle_seq, handle_seq, sisi_templ_seq, sisi_compl_seq1, sisi_compl_seq2])




#pat = re.compile(search_str)


def mkregexseqpermuts(seq):
    # Take a sequence and make som regex permutations.
    # wobble is a two-item tuple, making the extend of the wobble, typicall 0,5
    permuts = list()
    if wobble:
        permutfmt = r"[ATGC]{{{0[0]},{0[1]}}}".format(wobble)
    else:
        permutfmt = "[ATGC]"
    for i,nt in enumerate(seq):
        permuts.append(seq[:i]+")("+permutfmt+")("+seq[i+1:])
    ret = r"|".join(permuts)
    #print ret
    return ret

def refindallmatches(repattern, haystackstr):
    """ Like re.findall, but returns a list of matchobjects, not just the matching strings/groups.
        repattern must be a regular expression object, created with e.g. re.compile(...)
        if repattern is a string, it will be compiled.
    """
    res = list()
    match = True
    startpos = 0
    nmatch = 0
    while match:
        match = repattern.search(haystackstr,startpos)
        if not match:
            break
        startpos = match.end(1)
        res.append(match)
        nmatch += 1
        if nmatch > 20:
            print "refindallmatches(): Ending prematurely at 10 matches to avoid memory crash."
            break
    return res

def findallwithpermuts(seqtofind, haystackstr, Noverhang, wobble=None):
    """
    This searches for a string/seq in a longer string, but includes permutations
    of the sequence. E.g. if sequence is AACT, then search for <permut>ACT, A<permut>CT, AA<permut>T, AAC<permut>.
    If wobble is None, just search for a single mismatch.
    Ok, so if I really want to get a matching groups as 
    (before)(first)(wobble)(second)(after)
    then it becomes nearly impossible to use the extended (this1|orthis2|orthis3) search.
    This is a shame because the latter is faster than python looping.
    (?P<first_name>\w+) (?P<last_name>\w+)", "Malcolm Reynolds")
    """
    print "findallwithpermuts(): started with seq={}".format(seqtofind)
    res = list()
    permuts = list()
    patfmt = "(?P<before>{before})(?P<first>{first})(?P<wobble>{wobble})(?P<second>{second})(?P<after>{after})"
    before = "[ATGC ]{{{N}}}".format(N=Noverhang) 
    after = "[ATGC ]{{0,{N}}}".format(N=Noverhang)
    seq = seqtofind
    if wobble:
        permutfmt = r".{{{0},{1}}}".format(*wobble)
    else:
        permutfmt = "."
    for i,nt in enumerate(seq):
        wobbleskip = 0 if wobble else 1 # If we use wobbling, then do not skip any bases...
        permutfmt = nt # for testing
        repat = re.compile(patfmt.format(first=seq[:i], wobble=permutfmt, second=seq[i+wobbleskip:], before=before, after=after ) )
        print "findallwithpermuts: sending pattern '{}' to refindallmatches()".format(repat.pattern)
        res += refindallmatches(repat, haystackstr)
    #ret = r"|".join(permuts)
    print "findallwithpermuts completed with {} number of results".format(len(res))
    return res


def findmatchesofvariablelength(search_str, haystackstr, matchlen, Noverhang, wobble=None):
    res = list()
    nruns = 0
    for i in reversed(range(matchlen,len(search_str))):
        for j in range(0,len(search_str)-i):
            #res += re.findall(r"([ATGC]{{0,{1}}})({0})([ATGC]{{0,{1}}})".format(mkregexseqpermuts(search_str[j:j+i]),Noverhang), m13seq)
            #repat = re.compile(r"([ATGC]{{0,{1}}})({0})([ATGC]{{0,{1}}})".format(mkregexseqpermuts(search_str[j:j+i]),Noverhang))
            #res += refindallmatches(repat, m13seq)
            res += findallwithpermuts(search_str[j:j+i], m13seq, Noverhang, wobble=None)
            print "findmatchesofvariablelength(): {} number of res found for findallwithpermuts={}".format(len(res),search_str[j:j+i])
            nruns += 1
            if nruns > 20:
                print "findmatchesofvariablelength(): Ending prematurely at nruns {} to avoid memory crash...".format(nruns)
                return res
    return res

def mkalign(seq, match, Noverhang):
    """ seq is the antihandle seq, match is the match on the rcompl strand, Noverhang is how many on each side to print.
        The M13 seq is printed 3'-5', so this must be 5'-3'.
    """
    s = dnacomp(match)
    seq = seq[::-1] # make it 5'-3'.
    i = seq.find(s) # exact match; -1 if no match is found.
    if i == -1:
        # Matching is regex 
        #re.search(
        pass
    #print "s[i+len(match):] = {0}[{1}+{2}:]".format(s,i,len(match))
    #print "seq[i+len(match):] = {0}[{1}+{2}:] = {3}".format(seq,i,len(match), seq[i+len(match):])
    ret = ("{0:>{1}}".format(seq[:i],Noverhang), seq[i:i+len(match)], "{0:<{1}}".format(seq[i+len(match):],Noverhang)[:Noverhang] )
    print "{} + {} ({}) -> {} (i={})".format(seq, s, match, ret, i)
    return ret

def mkalign2(seq, match, Noverhang):
    """ Like mkalign, but takes a re MatchObject as match, not just a matched str.
    """
    s = dnacomp(match)
    seq = seq[::-1] # make it 5'-3'.
    i = seq.find(s) # exact match; -1 if no match is found.
    if i == -1:
        # Matching is regex 
        pass
    #print "s[i+len(match):] = {0}[{1}+{2}:]".format(s,i,len(match))
    #print "seq[i+len(match):] = {0}[{1}+{2}:] = {3}".format(seq,i,len(match), seq[i+len(match):])
    ret = ("{0:>{1}}".format(seq[:i],Noverhang), seq[i:i+len(match)], "{0:<{1}}".format(seq[i+len(match):],Noverhang)[:Noverhang] )
    print "{} + {} ({}) -> {} (i={})".format(seq, s, match, ret, i)
    return ret

def mydiff(tup):
    return max(tup)-min(tup)


def printmatchaligned(match, otherseq, Noverhang):
    """ 
    Like mkalign, but takes a re MatchObject as match, not just a matched str,
    and also does all the formatting here.
    """
#    template_line = "{0[0]}-{0[1]}[{0[2]}]{0[3]}-{0[4]} (M13)".format(match.groups())
    linefmt = "{0:>{N}}-{1}[{2}]{3}-{4:<{N}} ({strand})"
    #linefmt = "{0:>{N}}-{1}[{2}]{3}-{4:<{N}} ({strand})"
    linefmtnamed = "{before}-{first}[{wobble}]{second}-{after} ({strand})"
    template_line = linefmt.format(*match.groups(), strand="M13", N=Noverhang)
    # Ok, so now we have to align the other seq according to the template:
    # otherseq:      C ACG     TCT-GTTG-5'
    # template:   CAAT-TCG[AAC]AGA-ACTG-3'
    # re groups:  (1)  (2) (3) (4)  (5)
    # names     before first wobble second after
    #s = dnacomp(match)
    gd = match.groupdict()
    seq = otherseq[::-1] # make it 5'-3'.
    #i = seq.find(match.group(2)) # exact match; -1 if no match is found.
    i = seq.find(dnacomp(gd['first'])) # exact match; -1 if no match is found.
    #i = match.start('first') #tehe, nope, that refers to index in M13...
    j = seq.find(dnacomp(gd['second']),i+len(gd['first'])+len(gd['wobble'])) # exact match; -1 if no match is found.
    #j = match.start('second')
    # Nah, it is probably better to apply the original expression to the sequence
    otherseq_rcomp_patted = " "*10+dnarcomp(otherseq)+" "*10
#    print "Searching for {}\nin     '{}'".format(match.re.pattern, otherseq_rcomp_patted)
    other_match = re.search(match.re.pattern, otherseq_rcomp_patted)
#    print "other_match: {}".format(other_match)
#    if other_match:
#        print "spans for groups: {}".format(" - ".join(["{}={}".format(group, other_match.span(group)) 
#            for group in range(1,len(other_match.groups())+1) ]))
#    if j < 1:
#        j = i+len(gd['first'])+len(gd['wobble'])
#    if i == -1 or j == -1:
#        print "i or j == -1! ({},{})".format(i,j)
#        print "searched for: {} and {}".format(dnacomp(gd['first']), dnacomp(gd['second']))
#        print "in seq: {}\t-\t dnacomp: {}".format(seq, dnacomp(seq))
#        print "match.{field} = {val}".format(field="re.pattern", val=match.re.pattern)
##        print "\n".join(["match.{field} = match.{field}".format(match = match, field=field) for field in ["re.pattern"]])
##        print "\n".join(["match.{field} = {match.{field}}".format(field=field,match = match) for field in ["re.pattern"]])
#        print "match.groups(): {}".format(match.groups())
#        print "match.groupdict(): {}".format(match.groupdict())
#        exit()
    strparts = dict()
    # alternative, based on regex of otherseq:
    def getmatchtup(match, groupno): 
#        # other_string is printed 3'-5', so do not reverse.
#        print "match.string = {}".format(match.string)
#        print "match.span = {}".format(match.span())
#        print "slice:     '{}'".format(match.string[slice(*match.span(groupno))])
#        print "dnacomp = '{}'".format(dnacomp(match.string[slice(*match.span(groupno))]))
        return (dnacomp(match.string[slice(*match.span(groupno))]), mydiff(match.span(groupno)) )
    strparts['wobble'] = "{:^{}}".format(*getmatchtup(other_match, 3))
    #)  dnarcomp(other_match.string[slice(*other_match.span(3))]), mydiff(other_match.span(3)))# seq[i+len(gd['first']):j], len(gd['wobble']))
    strparts['before'] = "{0:>{1}}".format(*getmatchtup(other_match, 1))
    strparts['after'] = "{0:<{1}}".format(*getmatchtup(other_match, 5))
    strparts['first'] = "{0}".format(*getmatchtup(other_match, 2))
    strparts['second'] = "{0}".format(*getmatchtup(other_match, 4))
    strparts['strand'] = 'sisi'
    """ WORKING HERE """

    # based on index finding:
    if not (strparts['wobble'] == "{:^{}}".format(seq[i+len(gd['first']):j], len(gd['wobble'])) or \
           strparts['before'] == "{0:>{1}}".format(seq[:i],Noverhang)[:Noverhang] or \
           strparts['after'] == "{0:<{1}}".format(seq[j+len(gd['second']):],Noverhang)[:Noverhang] or \
           strparts['first'] == seq[i:i+len(gd['first'])] or \
           strparts['second'] == seq[j:j+len(gd['second'])]):
        print "ERROR, not the same."

    #print strparts
    handle_line = linefmtnamed.format(**strparts)
    #print handle_line
    #print template_line
    #print "s[i+len(match):] = {0}[{1}+{2}:]".format(s,i,len(match))
    #print "seq[i+len(match):] = {0}[{1}+{2}:] = {3}".format(seq,i,len(match), seq[i+len(match):])
    #ret = ("{0:>{1}}".format(seq[:i],Noverhang), seq[i:i+len(match)], "{0:<{1}}".format(seq[i+len(match):],Noverhang)[:Noverhang] )
    #print "{} + {} ({}) -> {} (i={})".format(seq, s, match, ret, i)
    return "\n".join([ #"{} vs {} (|{}) (^{}) (^|{})".format(match.groups(), otherseq, seq, dnacomp(otherseq), dnarcomp(otherseq)), 
                       #"i={},j={}, match.re.pattern={}".format(i,j, match.re.pattern),
                        template_line, handle_line])
    


#print "\n".join("{}".format(itm) for itm in res)

search_str = dnarcomp(antihandle_seq)
m13seq = sequences['M13mp18']
Noverhang = 5
matchlen = 6
myres = findmatchesofvariablelength(search_str, m13seq, matchlen, Noverhang, wobble=None)

#printstr = "\n-\n".join(["{0[0]}-{0[1]}[0[2]]{0[3]}-{0[4]} (M13)\n{1[0]}-{1[1]}-{1[2]} (sisi)".format(itm.groups(), mkalign(antihandle_seq, itm, Noverhang)) for itm in res])
print "Results:"
print map(lambda x: x.groups(), myres)
print "antihandle_seq is {}".format(antihandle_seq)
print "search_str is  :  {}".format(search_str)
if myres:
    printstr = "\n-\n".join(map(lambda x: printmatchaligned(x, antihandle_seq, Noverhang), myres))
    print printstr


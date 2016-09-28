#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2014 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

r"""

Module for matching sequence patterns.

Most of this is started in:
    Dropbox\_harvard_research\RNAi_Origami_project\Shared - Rasmus & Jaeseung\NUPACK\py\subseq_mutation_scan.py

Hint: To find recently changed python files, search with windows explorer in your dropbox folder
for the pattern "*.py" (including the quotation marks).

"""

import re
from itertools import product, chain, zip_longest

from rsseqgen import genparts


atgc = "ATGC"
basemap = dict(list(zip("ATGC", "TACG")))
def rcompl(seq):
    """ Returns reversed complement of seq. """
    return "".join(basemap[n] for n in reversed(seq))



def scanForPart(part, dataset):
    """
    Assumes dataset is list of tuples:
        (<seqname>, <sequence>, ...)
    """
    hits = [row[0] for row in dataset if part in row[1]]
    return hits


def patSeqGen(seqpat):
    """
    Creates a generator with actual sequences from a pattern.
    Currently only supports N->(ATGC) permutations.
    Usage (casted to list so easier to see):
    >>> list(patSeqGen("ATNGC"))
    ['ATAGC', 'ATTGC', 'ATGGC', 'ATCGC']
    """
    N_parts = re.findall("(N+)", seqpat)
    N_gens = [genparts(len(stretch)) for stretch in N_parts]
    # Make as tuple so it can be treated same as an N_generator:
    const_tups = [(part,) for part in seqpat.split('N') if part]
    # If seqpat starts with one or more N, insert empty element in front of const_tups
    # to make zipping consistent. (Alternatively, reverse order of izip...)
    if seqpat[0] == 'N':
        const_tups.insert(0, None)
        #pairs = izip_longest(N_gens, const_tups)
    #else:
    #    pairs = izip_longest(const_tups, N_gens)
    gens = (gen for gen in chain(*zip_longest(const_tups, N_gens)) if gen)
    return ("".join(comb) for comb in product(*gens))



def scanForPattern(pattern, dataset, hitcondition=None, sumcondition=None):
    """
    dataset: list of rows, where first field is name and second is sequence.
    hitcondition (function): part is considered a hit if hitcondition(part, fullseq) returns True.
        default is a hit if part is in fullseq,
        i.e. 'GGAAG' is a hit against the fullseq 'TTGGAAGCCC'.
    sumcondition (function): include matched part in result if sumcondition(part, matches) returns True.
        default is to include part if len(matches) == 0,
        i.e. the sequence was not found in the dataset.

    The use of hitcondition and sumcondition makes this function quite flexible.
    However, if either of these are excessively expensive, you should use a function
    more specialized/optimized for your use-case.
    """
    if hitcondition is None:
        hitcondition = lambda part, full: part in full
    if sumcondition is None:
        sumcondition = lambda x: len(x) == 0
    #seqs = [row[1] for row in dataset]
    return_parts = [] # list of tuples: (part, fount in, rev complement found in, match count, rcomp count, set count)
    parts = patSeqGen(pattern)
    for part in parts:
        if part == "GGTCC":
            print("Processing part '%s'" % part)
        matches = [row for row in dataset if hitcondition(part, row[1])]
        if sumcondition(part, matches):
            if part == "GGTCC":
                print("Part '%s' passed sumcondition '%s' with matches '%s'" % (part, sumcondition, matches))
            rcompl_matches = [row[0] for row in dataset if rcompl(part) in row[1]]
            #print "Part %s matches condition in %s oligos: %s (rcomplement in %s)" % (part, len(matches), ", ".join(matches), ", ".join(rcompl_matches))
            return_parts.append((part, matches, rcompl_matches, len(matches), len(rcompl_matches), len(set(matches)|set(rcompl_matches))))
        elif part == "GGTCC":
            print("Part '%s' did not pass sumcondition '%s', matches '%s'" % (part, sumcondition, matches))
    return return_parts

#rep = scanForRepeats(analyse_ds)

def noMatchNotPalindrome(part, matches):
    """ Convenience: Evaluates whether part is palindromic or matches is True. """
    if rcompl(part) == part: # Palindromic part
        return False
    if len(matches) > 0:
        return False
    return True

def partNotPalindrome(part, dummy):
    """ Convenience: Evaluates whether part is palindromic. """
    if rcompl(part) == part: # Palindromic part
        return False
    return True

def noMatchNotPalindromeHighGC(part, matches):
    """ Convenience: Evaluates whether part has matches or is palindromic or has high GC content. """
    if rcompl(part) == part: # Palindromic part
        return False
    if len(matches) > 0:    # Part found in existing dataset
        return False
    if float(sum(1 for N in part if N in "GC"))/len(part) < 0.6: # Low GC content
        return False
    if float(sum(1 for N in part if N in "GC"))/len(part) < 0.6: # Low GC content
        return False
    return True

def no3repeats(part, matches):
    """ Return true if part has 3 of same nucleotide in a row, e.g. AGGGC."""
    for N in "ATGC":
        if N*3 in part:
            return False
    return True


def makesubMatchWithExtra(sublength, extra5p='', extra3p=''):
    """
    Returns a closure (function with variables set) using given arguments.
    """
    def subMatch(part, fullseq):
        """
        Part is considered a hit if it does not have 4 nt in common with fullseq.
        Can optionally pad with extra seq.
        If the set of subparts is very long, factor out so subparts are only generated once per part.
        (Instead of being generated for every (part, fullseq) combination.)

        Returns True if part is a hit versus fullseq.
        """
        # Note: returns True for a hit.
        if part in fullseq:
            if part == "GGTCC":
                print("Part '%s' is in fullseq '%s'" % (part, fullseq))
            return True
        subparts = list(genparts(sublength, seqs=extra5p+part+extra3p)) # list for debugging
        # if part == "GGTCC":
        #     print "Comparing part '%s' subparts %s against %s" % (part, subparts, fullseq)
        for subpart in subparts:
            if subpart in fullseq:
                if part == "GGTCC":
                    print("Discarting part '%s', subpart '%s' in fullseq '%s'" % (part, subpart, fullseq))
                return True
        # if any(subpart in fullseq for subpart in subparts):
        #     return False
        return False
    return subMatch

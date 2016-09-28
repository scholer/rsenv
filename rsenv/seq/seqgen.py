#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

Includes code for sequence generation (and checks related to sequence generation).

This code is not really that good.
For production, consider using some of these other tools:
 - dsg from the CANADA package, http://ls11-www.cs.uni-dortmund.de/molcomp/downloads/dsg.jsp


"""

from math import log
from itertools import product, chain

from rsenv.utils.clipboard import get_clipboard, set_clipboard
from rsseq_util import *
atgc = "ATGC"

def endanchored_part_generator_simple(seq1, from_start=True, expanding=False):
    """
    Simple implementation:
    Developed for RS324
    """
    L = len(seq1)
    if from_start and expanding:
        return (seq1[:i+1] for i in xrange(L))
    elif from_start and not expanding:
        return (seq1[:L-i] for i in xrange(L))
    elif not from_start and expanding:
        return (seq1[i:] for i in xrange(L-2, 0, -1))
    elif not from_start and not expanding:
        return (seq1[i:] for i in xrange(L-1))

def endanchored_part_generator_halving(seq1, from_start=True, expand_part=True):
    """
    Developed for RS324
    Complex implementation:
    Solves the following problem: Let's say you have two long sequences.
    You know that the start of the two sequences match, but you don't know for how long.
    I assume the best a priori solution is to start guessing that half of seq1 matches seq2.
    If these 50% (1/2) doesn't match, then reduce to 25% (1/4) and check again.
    If this does match, then increase by 12.5% (1/8) and check if the 37.5% matches.
    If it does, then increase by 1/16 to 43.75%. No match? Decrease by 1/32 to 40.625%.
    Continue until you have decreased to only 1 nt and continue increasing or decreasing the offset
    (i.e. going right or left). When you have completed all steps, you have found the location.

    This will get the right position in log2(L)+1 attempts, and is deterministic in the number
    of attempts, as it will always require log2(L)+1 attemts.
    The alternative using the simple solution above (sequential, increasing by 1 until
    the position is found) requirees an average of L/2 attempts, and is not deterministic in
    the number of attempts.

    Usage:
    Use .send({'from_start': True/False, 'expand_part': True/False}) to control generator.
    * expand_part key controls whether to expand or contract the part w.r.t. the current size.
    * from_start key controls whether the part is from start to offset or offset to end.

    """
    directive = {'from_start': from_start, 'expand_part': expand_part}
    L = len(seq1)
    from_start_offset = 0
    from_end_offset = L
    # Adding a long iterator with ones to accomodate for rounding errors:
    fs_delta_generator = chain((L/2**i for i in xrange(1, int(log(L, 2))+1)), (1 for i in xrange(2)))
    fe_delta_generator = chain((L/2**i for i in xrange(1, int(log(L, 2))+1)), (1 for i in xrange(2)))
    while True:
        if directive['from_start']:
            delta = next(fs_delta_generator)
            from_start_offset += delta if directive['expand_part'] else -delta
            #print "delta is", delta, ", from_start_offset is", from_start_offset
            msg = yield seq1[:from_start_offset]
        else:
            # Wait... This should adapt to the result of the first search from the start.
            # Seems better to make a new generator.
            delta = next(fe_delta_generator)
            from_end_offset += -delta if directive['expand_part'] else delta
            #print "delta is", delta, ", from_end_offset is", from_end_offset
            msg = yield seq1[from_end_offset:]
        if msg:
            directive.update(msg)



def genparts(length, seqs=None):
    """
    This function has two use cases:
    1) Returns a generator of all possible sequences of length <length>.
    2) Return a generator of all "sliding sequence frames" (if seqs is provided).
    Examples (cast to list to make it easier to see the result):
    >>> list(genparts(3))
    ['AAA', 'AAT', 'AAG', 'AAC', 'ATA', 'ATT', 'ATG', 'ATC', 'AGA', 'AGT', 'AGG', 'AGC', 'ACA', 'ACT', 'ACG', 'ACC',
    'TAA', 'TAT', 'TAG', 'TAC', 'TTA', 'TTT', 'TTG', 'TTC', 'TGA', 'TGT', 'TGG', 'TGC', 'TCA', 'TCT', 'TCG', 'TCC',
    'GAA', 'GAT', 'GAG', 'GAC', 'GTA', 'GTT', 'GTG', 'GTC', 'GGA', 'GGT', 'GGG', 'GGC', 'GCA', 'GCT', 'GCG', 'GCC',
    'CAA', 'CAT', 'CAG', 'CAC', 'CTA', 'CTT', 'CTG', 'CTC', 'CGA', 'CGT', 'CGG', 'CGC', 'CCA', 'CCT', 'CCG', 'CCC']
    >>> list(genparts(3, "ACGTTG"))
    ['ACG', 'CGT', 'GTT', 'TTG']
    """
    if seqs is None:
        return ("".join(comb) for comb in product(atgc, repeat=length))
    if isinstance(seqs, str):
        combseq = seqs
    else:
        combseq = "".join(seqs)
    return (combseq[i:i+length] for i in range(len(combseq)-length+1))


def seqPermuts(seqs=None, permlen=5, copyToClipboard=False, includerevcompl=False, returnFlatList=True):
    """
    Do permutations of the sequence in stretches of permlen.
    Example: seqPermuts("ATGTAAGGTGA", 4) will return:
    ["ATGT", "TGTA", "GTAA", "TAAG", "AAGG", "AGGT", "GGTG", "GTGA"]
    seqs can also be a list of strings.
    if seqs is None, it will read from clipboard.
    If copyToClipboard is True, it will send the result to the clipboard.

    """

    if seqs is None:
        get_clipboard()
    if isinstance(seqs, str):
        seqs = [seq.replace(",", "").strip() for seq in seqs.split()]

    if includerevcompl:
        seqs += dnarcomp(seqs)

    if returnFlatList:
        permuts = list()
        for seq in seqs:
            #for i,v in enumerate(seq):
            for i in range(len(seq)-permlen):
                permuts.append(seq[i:i+permlen])
    else:
        permuts = [[seq[i:i+permlen] for i in range(len(seq)-permlen)] for seq in seqs]
    if copyToClipboard:
        set_clipboard(",".join(seqs))

    return permuts


def testSeqPermuts():
    """
    Note that it is only possible to produce 4**4/2 = 128 different 4-mers
    (in half as the reverse compl should not be included)
    On the other hand, 5-mer permutations can produce 1562 unique sequences.
    (however, putting those together will produce repeated sequences at the joints)
    """
    existingHandles = """
    GGGCTCATGCGAGGCTGTATGT
    TTCCTCTACCACCTACATCAC
    GGTCGTGTTCGATCAGAGCGC
    GTTGAGTCCTGTCAC
    GTTGCATCCTCCAAC
    GTGCAGACAAC
    CGGGAACCGCGTATCTTGCCA
    CGGTTCATAACGGAACCGCCG
    GATTCGGGAAGCAAACCCGCG
    CCAGTACGCGGCGTAGTACCC
    CGGAATACTTGAATCGGGTTC
    GCCAGCTCAGCC
    """
    #existingHandles=existingHandles.split()
#    permuts = seqPermuts(existingHandles[0])
    permuts = seqPermuts(existingHandles, permlen=5, copyToClipboard=True, includerevcompl=True)
    print(existingHandles)
    print(",".join(permuts))

    permuts4 = seqPermuts(existingHandles, permlen=4, includerevcompl=True)

    permuts4 = [seq for seq in permuts4 if sum([x.upper() in "GC" for x in seq])>2]

    print(",".join(permuts4))


def checkMatch(needle, haystack):
    pass


def checkCandidates(candlist, existingSet, permlen=5):
    """
    Screen candidates against an existing set of oligos,
    returning candidates that do not share similarity with oligos in the existing set.
    Currently, two oligos are considered "similar" if they have a stretch of <permlen>
    that is identical between the two.
    Returns a tuple with (candidates, matchdata)
    This function uses set logic, so order is NOT maintained.
    """
    candidates = copy(candlist) # Otherwise, you might make alterations to the existing list !!
    candidates += dnarcomp(candidates) # Need to do this before so we can reference them.
    candidates5mers = seqPermuts(candidates, permlen=permlen, includerevcompl=False, returnFlatList=False)
    #print candidates5mers
    matchdata = [[[(i, candidates[i], cand5mer, existing) for existing in existingSet if cand5mer in existing]
                                                for cand5mer in cand5mers]
                                            for i, cand5mers in enumerate(candidates5mers)]
    match5mer = {match[0] for candidate5mers in candidates5mers for cand5mer in candidate5mers for match in cand5mer}
    candidates = set(candidates) - match5mer # set algorithmics. Just make sure both are sets.
    return candidates, matchdata

    # Interpreting "incomprehensible list comprehensions":
    # Essentially just expand to:
#    for candidate5mers in candidates5mers:
#        for cand5mer in candidate5mers:
#            for match in cand5mer:
#                match[0]
    # (or, if starting by the expanded for-loop construct, contract by removing
    # extra characters and move h to the beginning.)


def testcheckCandidates(candidates=None):
    # All handles down to rs4a.
    existingSet = """
    ACATACAGCCTCGCATGAGCCC GGGCTCATGCGAGGCTGTATGT TTCCTCTACCACCTACATCAC GGTCGTGTTCGATCAGAGCGC
    gtgatgtaggtggtagaggaa gcgctctgatcgaacacgacc GTTGAGTCCTGTCAC GTTGCATCCTCCAAC GTGCAGACAAC
    CGGGAACCGCGTATCTTGCCA TGGCAAGATACGCGGTTCCCG CGGTTCATAACGGAACCGCCG CGGCGGTTCCGTTATGAACCG
    GATTCGGGAAGCAAACCCGCG CGCGGGTTTGCTTCCCGAATC CCAGTACGCGGCGTAGTACCC GGGTACTACGCCGCGTACTGG
    CGGAATACTTGAATCGGGTTC GAACCCGATTCAAGTATTCCG""".upper().split()
    if not candidates:
        candidates = [
"GCCAGCTCAGCC", # an actual candidate (rs6h at time of writing). However, shares GCTCA with #2, rs0a..
#"AAAAAAAAAAAA", # test, no matches
#"TTTTTTTTTTTT", # test, no matches
#"ACATACAGCCTC", # From the first, should produce all 7 matches.
#"CTTACTTTCTCT", # From second-last (now erased). Notice that TACTT is shared also with the fourth last.
"GACTCCGATACAAGTATTCCG", # third-last, with some alterations, should match.
"GATCCGGATACAGGTCTTGCG" # third-last, with some alterations. Still matches other strands, though.
        ]
    cand, matchdata = checkCandidates(candidates, existingSet, permlen=5)
    print("Candidates (after filter):")
    print(cand)
    print("Matchdata:")
    from pprint import pprint
    pprint(matchdata)
#    for candidate5mers in matchdata:
#        for cand5mer in candidate5mers:
#            for match in cand5mer:
#                print match


def generateRandomSeqs(seqlength, desiredseqs, haltAfter=10000, verbose=False, permlen=5, newseq="semi-random"):
    """
    Can also be implemented as iterator...
    """
    def semirandomnewseq(seq):
        return "".join([N if randint(0, 1) else nucs[randint(0, 3)] for N in seq])
    def randomnewseq(seq):
        return "".join([nucs[randint(0, 3)] for N in seq])
    if newseq == "semi-random":
        print("Using SEMIrandom-style new sequence generator")
        newseqgen = semirandomnewseq
    else:
        print("Using random-style new sequence generator")
        newseqgen = randomnewseq

    seqs = set() # Could also be a dict...
    hits = list()
    usedpermuts = set() # We might as well keep a list of 5mers in use...
    failedseqs = set()
    seqs_len = 0
    nucs = "ATGC"
    GCcontent = (0.4, 0.7)
    # Many approaches, either systematic, random or mathematically clever. I go with random...
    from random import randint
    seq = "".join([nucs[randint(0, 3)] for i in range(seqlength)])
    # Not sure what is better, have as list or cast to tuple/generator/whatever (must be hashable)
    nTries = 0
    while nTries < haltAfter and len(seqs) < desiredseqs:
        nTries += 1
        # Not sure if it is better to just produce completely new random or keep some?
        # Keeping every other generates an average of 20 in 1'000'000 tries with permlen=5 (5 for permlen=4)
        # Pretty much the same for completely random new seq. :-/
#        seq2 = "".join([N if randint(0,1) else nucs[randint(0,3)] for N in seq])
#        seq2 = "".join([nucs[randint(0,3)] for N in seq])
        seq2 = newseqgen(seq)
        if seq2 not in seqs and seq2 not in failedseqs:
            if GCcontent[0] < float(sum([N in "GC" for N in seq2]))/len(seq2) < GCcontent[1]:
                #print nTries
                permuts = seqPermuts(seq2, permlen=permlen, includerevcompl=True)
                # saving all failed sequences may produce a large memory overhead:
                if any([permut in usedpermuts for permut in permuts]):
#                    #failedseqs.add(seq2)
                    pass
                elif any([avoidseq in seq2 for avoidseq in ["AAAA", "TTTT", "GGGG", "CCCC", "GCGCGC", "CGCGCG"]]):
                    failedseqs.add(seq2)
                else:
                    if verbose:
                        print("{1}: {0}/{3} New sequence: {2}".format(len(seqs), nTries, seq2, desiredseqs))
                    seqs.add(seq2)
                    usedpermuts.update(set(permuts))
                    seq=seq2
                    hits.append((len(seqs), nTries))
    #return (seqs, usedpermuts, failedseqs, nTries)
    return (list(seqs), hits, nTries) # returning as list not set in order to serialize with JSON.

def test_generateRandomSeqs():
    """
    It might be fun to do a comparison of the rate profile for all-random-new-seq vs half-random and plot them.
    From what I can tell, the completely random shoots up faster, but then fails to find anything.
    The semi-random does not find as many initially, but ends at the same level.
    """
#    (seqs, usedpermuts, failedseqs, nTries) = generateRandomSeqs(20, 50, 10000, verbose=True, permlen=5, newseq="random")
#    print "Sequences in {0} tries".format(nTries)
#    print seqs

    newseq_methods = ["semi-random", "random"]
    runs = 4
    max_tries = 1e7 # I tested
    results = dict([(newseq,
                    [generateRandomSeqs(20, 100, 1e8, verbose=True, permlen=5, newseq=newseq) for i in range(runs)]) for newseq in newseq_methods])
    import json
    json.dump(results, open("test_generateRandomSeqs_results2.json", "wb"))
    # To parse and print, do:
    # import json; res = json.load(open(...))
    # all = "\n".join([seq for methodkey,methodres in res.items() for run in methodres for seq in run[0]]

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
def dnacomplement(a, reverse=True):
    print "dnacomplement; does ''.join([wcmap[x] for x in a.lower()])[::-1]"
    wcmap = {"t":"a","a":"t","T":"A","A":"T",
             "c":"g","g":"c","C":"G","G":"C",
             " ":" "}
    complement = ''.join([wcmap[x] for x in a.lower()])
    if reverse:
        return complement[::-1]   #([start:end:slice])
    else:
        return complement
    
    # Alternatively, brug af map function i stedet for for loop)
    b = "".join(map(lambda x: wcmap[x], a.lower())[::-1])


""" Simpler code, copy/pasted on cadnano (credit to Nick, Shawn, et al.)
    I have only changed notations and added space etc to the map.
"""
import string
dnacomplementmap = string.maketrans('ACGTacgt ','TGCATGCA ')
def dnarcomp(seqStr):
    """Returns the reverse complement of the sequence in seqStr.
    if seqStr is not a basestring, it will return a list of the
    reverse complement of each entry.
    """
    if isinstance(seqStr, basestring):
        return seqStr.translate(dnacomplementmap)[::-1]
    else:
        # Assume list of strings:
        return [seq.translate(dnacomplementmap)[::-1] for seq in seqStr]
def dnacomp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(dnacomplementmap)


""" 
----------------------
--- CADNANO stuff ----
----------------------

See also:
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools/file_transformation

"""




""" Parsing, handling and manipulating set file information """

def appendSequenceToStaps(staplesetfilepath, appendSeq, filtercolor=None, appendToFivePrime=False,
    isComplement=False, desc="", verbose=0, outsep='\t', writeToFile=True, appendToFile=False):
    """ A bit similar to /oligomanager/tools/file_transformation/sequencemapper.py
    Function: Will read file given in staplesetfilepath, and to all sequences
    given in filtercolor it will append sequence given by appendSeq.
    Result is output to file (input filename with 'append' postfix), unless
    writeToFile is False, in which case result is printed to a StringIO object
    and returned.
    Note: First line is considered to be a header line.
    params:
        filtercolor : Only consider lines where 'Color' field has this value. Default is None (consider all input fields)
        appendToFile: Append to output file, rather than write a new file. Default is False.
        isComplement: If true, will use the reverse complement of the given sequence. Default is False.
        desc        : Description to add to all output sequences.
        verbose     : Output all lines that are also printed to file.
        outsep:       Force this as the field separator in output file. 
                      Set to None to use same separator as input file. Default is '\t'.
        writeToFile : If false, will write all lines to a StringIO object which is returned. Default is True.
        appendToFivePrime: If true, append appendSeq to 5' end of input sequence. Default is False (appends to 3').
        
    """
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
        # simple test for whether to use comma or tab as separator:
        testline = fp.readline().strip()
        sep = '\t' if (len(testline.split('\t')) > len(testline.split(','))) else ','
        if outsep is None: outsep = sep
        header = testline.split(sep)
        # Header map: maps a header string to column index
        hm = dict([(v,i) for i,v in enumerate(header)])
        fp.seek(0)
        for line in fp:
            row = line.strip().split(sep)
            if filtercolor is None or (len(row)>1 and (row[hm['Color']] == filtercolor or row[hm['Color']] in filtercolor)) :
                seq = row[hm['Sequence']]
                Start = row[hm['Start']]
                if appendToFivePrime:  seq = "".join([appendSeq, seq])
                else:       seq = "".join([seq, appendSeq])
                ln = "{0}:{1}\t{2}\t{3}".format(desc,Start, seq, len(seq)) if desc else seq
                if verbose: print ln
                newfile.write(ln+"\n")
    if writeToFile:
        newfile.close()
    else:
        return newfile








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
        import gtk
        seqs = gtk.clipboard_get().wait_for_text()
    
    if isinstance(seqs, basestring):
        seqs = [seq.replace(",","").strip() for seq in seqs.split()]

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
        import gtk
        gtk.clipboard_get().set_text(",".join(seqs))
    
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
    """
    #existingHandles=existingHandles.split()
#    permuts = seqPermuts(existingHandles[0])
    permuts = seqPermuts(existingHandles, permlen=5, copyToClipboard=True, includerevcompl=True)
    print existingHandles
    print ",".join(permuts)
    
    permuts4 = seqPermuts(existingHandles, permlen=4, includerevcompl=True)
        
    permuts4 = filter(lambda seq: sum(map(lambda x: x.upper() in "GC", seq))>2, permuts4)
    
    print ",".join(permuts4)


def checkMatch(needle, haystack):
    pass


def checkCandidates(candidates, existingSet, permlen=5):
    """
    Screen candidates against an existing set of oligos, 
    returning candidates that do not share similarity with oligos in the existing set.
    Currently, two oligos are considered "similar" if they have a stretch of <permlen>
    that is identical between the two.
    Returns a tuple with (candidates, matchdata)
    This function uses set logic, so order is NOT maintained.
    """
    candidates += dnarcomp(candidates) # Need to do this before so we can reference them.
    candidates5mers = seqPermuts(candidates, permlen=permlen, includerevcompl=False, returnFlatList=False)
    print candidates5mers
    matchdata = [[[(i, candidates[i], cand5mer, existing) for existing in existingSet if cand5mer in existing]
                                                for cand5mer in cand5mers]
                                            for i,cand5mers in enumerate(candidates5mers)]
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


def testcheckCandidates():
    existingSet = """
    ACATACAGCCTCGCATGAGCCC GGGCTCATGCGAGGCTGTATGT TTCCTCTACCACCTACATCAC GGTCGTGTTCGATCAGAGCGC
    gtgatgtaggtggtagaggaa gcgctctgatcgaacacgacc GTTGAGTCCTGTCAC GTTGCATCCTCCAAC GTGCAGACAAC
    CGGGAACCGCGTATCTTGCCA TGGCAAGATACGCGGTTCCCG CGGTTCATAACGGAACCGCCG CGGCGGTTCCGTTATGAACCG
    GATTCGGGAAGCAAACCCGCG CGCGGGTTTGCTTCCCGAATC CCAGTACGCGGCGTAGTACCC GGGTACTACGCCGCGTACTGG
    CGGAATACTTGAATCGGGTTC GAACCCGATTCAAGTATTCCG""".upper().split()
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
    print "Candidates (after filter):"
    print cand
    print "Matchdata:"
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
        return "".join([N if randint(0,1) else nucs[randint(0,3)] for N in seq])
    def randomnewseq(seq):
        return "".join([nucs[randint(0,3)] for N in seq])
    if newseq == "semi-random":
        print "Using SEMIrandom-style new sequence generator"
        newseqgen = semirandomnewseq
    else:
        print "Using random-style new sequence generator"
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
    seq = "".join([nucs[randint(0,3)] for i in range(seqlength)])
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
                        print "{1}: {0}/{3} New sequence: {2}".format(len(seqs), nTries, seq2, desiredseqs)
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
    json.dump(results, open("test_generateRandomSeqs_results.json", "wb"))



if __name__ == "__main__":
    """ Testing """

#    testSeqPermuts()
#    testcheckCandidates()

    test_generateRandomSeqs()

#    thomasseq =   "ACATACAGCCTCGCATGAGCCC"
#    rcomplement = "GGGCTCATGCGAGGCTGTATGT"
#    #useseq =      "GGGCTCATGCGAGGCTGTATGTTT" # with a 2-T linker to minimize strain
#    useseq = "GTG CAG ACA AC T".replace(' ','')
#    # Edit: Actual sisi-linker should be on 3' end, sequence is GTGCAGACAAC
#    #appendSequenceToStaps('TR.ZS.i-4T.set', useseq, filtercolor="#03b6a2", desc="TR:col02-ss", appendToFivePrime=True)
#    #appendSequenceToStaps('TR.ZS.i-4T.set', useseq,   filtercolor="#1700de", desc="TR:col08-ss", 
#    #                        appendToFivePrime=True, appendToFile=True, isComplement=False)
#    appendSequenceToStaps('TR.ZS.i-4T.set', useseq, filtercolor="#03b6a2", desc="TR:col02-ss", appendToFivePrime=True)


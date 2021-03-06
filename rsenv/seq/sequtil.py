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

Includes various python code that I use frequently for manipulating DNA sequences.
"""

import re
import string

atgc = "ATGC"
basemap = dict(list(zip("ATGC", "TACG")))


def rcompl(seq):
    """ Returns reversed complement of seq. """
    return "".join(basemap[n] for n in reversed(seq))
    # Alternatively, use map instead of for for loop)
    # b = "".join(map(lambda x: {"t": "a", "a": "t", "c": "g", "g": "c"}[x], a.lower())[::-1])


def compl(seq):
    """ Returns reversed complement of seq. """
    return "".join(basemap[n] for n in seq)


def dnastrip(a):
    """ Easy stripping of all characters except ATGC. """
    #print "return ''.join(x for x in a.upper() if x in 'ATGC')"
    return ''.join(x for x in a.upper() if x in 'ATGC')

"""
Here is another alternative using build-in filter function and lambda expression:
b = filter(lambda x: x in 'ATGC', a)
lambda functions are a short-hand way to write simple, anonymous functions. Many similar use-cases, e.g.: map(lambda x: x**3, (1,2,3))
Albeit anonymous, references to lambdas can be assigned like such: l = lambda x: x**3
"""


def dnaformat(a):
    """ Add space for every 8th base:"""
    b = dnastrip(a)
    return ''.join([(letter+' ' if i % 8 == 7 else letter) for i, letter in enumerate(b)]).strip()


def reverse(a):
    """ Reverse sequence """
    print("return a[::-1]   #([start:end:slice])")
    return a[::-1]   #([start:end:slice])


def dnacomplement_3to5p(a):
    """ Complementary sequence (reading 3to5 prime; useful for underlaying sequences) """
    return ''.join([{"t":"a","a":"t","c":"g","g":"c"}[x] for x in a.lower()])   #([start:end:slice])



def dnacomplement(a, reverse=True):
    """ Reverse complementary sequence """
    print("dnacomplement; does ''.join([wcmap[x] for x in a.lower()])[::-1]")
    #wcmap = {"t":"a","a":"t","T":"A","A":"T",
    #         "c":"g","g":"c","C":"G","G":"C",
    #         " ":" "}
    # easier way to generate:
    wcmap = dict(list(zip("ATGC ", "TACG ")))
    a = a.upper()
    if reverse:
        a = reversed(a)
    complement = ''.join(wcmap[x] for x in a if x in wcmap)
    return complement
    #if reverse:
    #    return complement[::-1]   #([start:end:slice])
    #else:
    #    return complement

    # Alternatively, brug af map function med lambda i stedet for list comprehension:
    # b = "".join(map(lambda x: wcmap[x], a.lower())[::-1])


"""
Simpler code, copy/pasted on cadnano (credit to Nick, Shawn, et al.),
uses string.maketrans and str.translate() to translate one string to another.
I have only changed notations and added space etc to the map.
(requires string to be imported.)
"""
try:
    # Note: This is NOT a direct basepair mapping, but a char-point map,
    # which must be passed to str.translate()
    dna_wc_bp_table = str.maketrans('ACGTacgt ', 'TGCATGCA ')
except AttributeError:
    dna_wc_bp_table = string.maketrans('ACGTacgt ', 'TGCATGCA ')


def dnarcomp(sequence):
    """Returns the reverse complement of the sequence in sequence.
    if sequence is not a basestring, it will return a list of the
    reverse complement of each entry.
    """
    if isinstance(sequence, str):
        return sequence.translate(dna_wc_bp_table)[::-1]
    else:
        # Assume list of strings:
        return [seq.translate(dna_wc_bp_table)[::-1] for seq in sequence]


def dnacomp(seqStr):
    """Returns the complement of the sequence in seqStr."""
    return seqStr.translate(dna_wc_bp_table)


def sequence_wo_mods(seq, format="IDT"):
    """

    :param seq:
    Returns:
        sequence without modifications.
    """
    mods_pat = r'\/\w*\/'
    # replace all instances of pattern with '':
    return re.sub(mods_pat, '', seq)


def sequence_pure(seq):
    seq = seq.replace(" ", "").replace("-", "").replace("*", "")
    seq = sequence_wo_mods(seq)
    return seq







if __name__ == "__main__":
    """ Testing """

#    test_seq_permuts()
#    test_check_candidates()

    # test_generateRandomSeqs()

#    thomasseq =   "ACATACAGCCTCGCATGAGCCC"
#    rcomplement = "GGGCTCATGCGAGGCTGTATGT"
#    #useseq =      "GGGCTCATGCGAGGCTGTATGTTT" # with a 2-T linker to minimize strain
#    useseq = "GTG CAG ACA AC T".replace(' ','')
#    # Edit: Actual sisi-linker should be on 3' end, sequence is GTGCAGACAAC
#    #append_sequence_to_staps('TR.ZS.i-4T.set', useseq, filtercolor="#03b6a2", desc="TR:col02-ss", appendToFivePrime=True)
#    #append_sequence_to_staps('TR.ZS.i-4T.set', useseq,   filtercolor="#1700de", desc="TR:col08-ss",
#    #                        appendToFivePrime=True, appendToFile=True, isComplement=False)
#    append_sequence_to_staps('TR.ZS.i-4T.set', useseq, filtercolor="#03b6a2", desc="TR:col02-ss", appendToFivePrime=True)

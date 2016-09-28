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
"""

Module for diff'ing sequences (not directly aligning).

"""

from collections import namedtuple

from .seqgen import endanchored_part_generator_simple, endanchored_part_generator_halving

def binary_insert_diff(seq1, seq2):
    """
    Compares two sequences with matching ends in order to locate the insert.
    The ends must be matching.
    Returns None if matching fails.
    Example:
    >>> seq1 = "TACCCGGGGATCCT                                                           CTAGAGTCGACCTGCAGGCA".replace(' ', '')
    >>> seq2 = "TACCCGGGGATCCTTATACGGGTACTAGCCATGCGTATACGGTCGCTAGCGGACTTGCCTCGCTATCAAAGGTCTAGAGTCGACCTGCAGGCA"
    >>> binary_insert_alignment(seq1, seq2)
    (   'TACCCGGGGATCCT',   # Common start part
        '',                 # Non-matching part of seq1
        'TATACGGGTACTAGCCATGCGTATACGGTCGCTAGCGGACTTGCCTCGCTATCAAAGGT',  # Non-matching part of seq2
        'CTAGAGTCGACCTGCAGGCA') # Common end part
    """
    part_generator = endanchored_part_generator_halving
    part_generator_simple = endanchored_part_generator_simple
    seq1_part_gen = part_generator(seq1)
    #start_found = end_found = False
    start_part = end_part = ''
    #from_start_offset = from_end_offset = 0
    part = next(seq1_part_gen)
    # We need to exhaust the generator to be sure that we have found the right part (the last delta is 1)
    #for part in seq1_part_gen:
    try:
        while True:
            if part == seq2[:len(part)]:
                start_part = part # save
                msg = {'expand_part': True}
            else:
                msg = {'expand_part': False}
            part = seq1_part_gen.send(msg)
    except StopIteration:
        pass
    # Edit: Instead of searching "the end part", it is better to create a new part_generator
    # which is adapted to not include the common start part.
    #seq1_part_gen = part_generator(seq1[len(start_part):], from_start=False)
    #part = seq1_part_gen.next() # Must send None or use next() on a just-started generator.
    #try:
    #    while True:
    #        if part == seq2[-len(part):]:
    #            end_part = part
    #            msg = {'expand_part': True}
    #        else:
    #            print "part did not match:", part, "!=", seq2[-len(part):]
    #            msg = {'expand_part': False}
    #        part = seq1_part_gen.send(msg)
    #except StopIteration:
    #    pass
    ## Edit2: In fact, now that you have located the start of the non-matching part,
    ## it is probably much better to have a simple part generator that starts from the start.
    seq1_part_gen = part_generator_simple(seq1[len(start_part):], from_start=False, expanding=False)
    #for part in seq1_part_gen:
    #    if part == seq2[-len(part):]:
    #        end_part = part
    #        break
    end_part = next((part for part in seq1_part_gen if part == seq2[-len(part):]), '')
    MatchTup = namedtuple('MatchTup', ['common_start', 'seq1_nonmatch', 'seq2_nonmatch', 'common_end'])
    #print "start_part:", start_part, ", end_part:", end_part
    #print "seq1[len(start_part):-len(end_part) =", seq1[len(start_part):len(seq1)-len(end_part)]
    #print "seq2[len(start_part):-len(end_part)] =", seq2[len(start_part):len(seq2)-len(end_part)]
    # seq1[len(start_part):-len(end_part)] is equal to seq1[len(start_part):len(seq1)-len(end_part)]
    # EXCEPT for when len(end_part) is zero, seq1[2:0] is just '' and seq1[2:-1] does not include the last element.
    ret = MatchTup(start_part, seq1[len(start_part):len(seq1)-len(end_part)],
                   seq2[len(start_part):len(seq2)-len(end_part)], end_part)
    return ret


    #while not start_found:
    #    if part == seq2[:len(part)]:
    #        # Two cases, either we have the correct length, or
    #        start_found = True
    #        from_start_offset = len(part)
    #        # new part, for end search:
    #        part = seq1_part_gen({'from_start': False, 'expand_part': True})
    #    else:
    #        if part in seq2[:len(part)]:

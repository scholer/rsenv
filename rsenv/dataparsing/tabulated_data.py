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

Module for parsing tabulated data.


"""

#from itertools import chain
import itertools
import logging
logger = logging.getLogger(__name__)


def tabdata_as_dictlist(tabdata, headers=None, sepcands=('\t', ',', ';'), sep=None, stripcells=True):
    """
    Arguments:
        tabdata: iterable, e.g. lines in a file.
        headers: list of column names.
            if header is None, the first line is assumed to be the header.
        sepcands: If sep is None, find the best sep candidate from this sequence.
        stripcells: If true, will strip whitespace from values after splitting lines to cells.
        #nskip : skip N number of lines.
    Usage:
        tab_data = "\
header1, header2\
333, 55".strip().split('\n')
        tabdata_as_dictlist(tab_data)

    See also:
    * The built-in csv module. This has a more advanced csv.DictReader
        class that supports text quotation marks, etc.
    * pandas.from_csv()
    """
    if sep is None:
        sampleline = next(tabdata)
        sep = get_sep_from_line(sampleline, sepcands)
    else:
        sampleline = None
    if headers is None:
        if sampleline is None:
            sampleline = next(tabdata)
        headers = sampleline.split(sep)
    # What if headers is not None, but we had to read a sampleline to extract sep ?
    elif sampleline:
        tabdata = itertools.chain((sampleline, ), tabdata)

    # Make dictlist:
    rows = (line.split(sep) for line in tabdata)
    if stripcells:
        rows = ([cell.strip() for cell in row] for row in rows)
    #rows = list(rows)
    #for row in rows:
    #    print zip(headers, row)
    dictlist = [dict(list(zip(headers, row))) for row in rows]
    return dictlist


def get_sep_from_line(line, sepcands=('\t', ',', ';'), method='presence'):
    """
    Returns sep from line.
    Raises ValueError if a candidate was not found.
    """
    if method == 'presence':
        for sep in sepcands:
            if sep in line:
                return sep
    elif method == 'maxcount':
        maxcount, bestsep = sorted((line.count(sep), sep) for sep in sepcands)[0]
        if maxcount > 0:
            return bestsep
    raise ValueError("Error, none of the candidates are present in the line.")







def findFieldByHint(candidates, hints):
    """
    Takes a list of candidates, e.g.
        ['Pos', 'Sequence', 'Volume']
    and a hint, e.g. 'seq' or a (prioritized!) list of hints, e.g.
        ('sequence', 'seq', 'nucleotide code')
    and returns the best candidate matching the (case-insensitive)
    hint(s) e.g. for the above arguments, returns 'Sequence'.
    If more than one hint is given, the first hint that yields a
    resonable score will be used. In other words, this function will
    NOT screen ALL hints and use the best hint, but only use the next
    hint in the sequence if the present hint does not yield a resonable
    match for any of the candidates.
    Thus, the hints can be provided with decreasing level of specificity,
    e.g. start with very explicit hints and end with the last acceptable
    hint, e.g. the sequence: ('Well position', 'Rack position', 'Position', 'Well Pos', 'Well', 'Pos')
    If no candidates are suited, returns None.

    """
    if not isinstance(hints, (list, tuple)):
        hints = (hints,)
    def calculate_score(candidate, hint):
        """
        Compares a candidate and hint and returns a score.
        This is not intended to be "align" based, but should return
        a "probability like" value for the change that the candidate
        is the right choice for the hint.
        """
        score = 0
        if candidate in hint:
            # candidate is 'seq' and hint is 'sequence'
            # However, we do not want the hint 'Rack position' to yield
            # high score for the candidate e.g. 'Rack name', nor do we want
            # 'sequence' to yield a high score for the field 'sequence name'
            score += 0.1 + float(len(candidate))/len(hint)
        if hint in candidate:
            score += 1 + float(len(hint))/len(candidate)
        return score
    for hint in hints:
        scores = [calculate_score(candidate.lower(), hint.lower()) for candidate in candidates]
        #print "="
        scores_list = [cand+"({}) ({:.3f})".format(type(cand), score) for cand, score in zip(candidates, scores)]
        #print scores_list
        scores_str = ", ".join(scores_list)
        #print scores_str
        #print "--------"
        # do NOT attempt to use u"string" here, doesn't work?
        logger.debug("Candidate scores for hint '%s': %s", hint, scores_str)
        if max(scores) > 0.2:
            return candidates[scores.index(max(scores))]
        #for candidate in candidates:
        #    if hint in candidate.lower():
        #        return candidate
    # None of the hints were found in either of the options.
    return None

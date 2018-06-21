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
##
# pylint: disable-msg=W0612,R0903
"""
Module with various file-related utility functions.
Brutally taken from the old staplemixer.FileHelper object and
split into functions rather than having an unnessecary class helper.

This contains all functions relevant to (csv) files.

Functions specific to rackfiles (*.rack.csv) should be placed
in rackfileutils.py




"""

import csv
import re
## Logging:
import logging
logger = logging.getLogger(__name__)



class Csvdialect(csv.excel_tab):
    """
    Used in place of csv.Dialect.
    """
    def __init__(self, *args, **kwargs):
        csv.excel_tab.__init__(self, *args, **kwargs)
        self.newline = '\n'
        self.delimiter = '\t'

def natural_sort(l):
    """
    Natural sorting algorithm,
    from http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)



def read_csvfile(inputfn):
    """
    Reads a standard one-rack-per-file csv data file.
    """
    with open(inputfn, 'rU') as fd:
        datastruct = gen_csv_data(fd) # Make sure to store as list before closing file.
    return datastruct


def getcsvskiprows(fd, delimiters=None):
    """
    Sometimes csv files has some extra header info before the header row.
    This function will try to:
    1) Seek the file to the right position between the header info and the header row.
    2) Return the number of header info lines (nskiprows) and the position of the header row.

    Returns None if no header row was encountered.

    Example usage:
    >>> getcsvskiprows(fd)
    (12, 505)
    >>> getcsvskiprows(fd)
    (0, 505)
    >>> fd.readline()
    "Cat,Oligo#,Type[scale],MP,Purification,,[line] Name,Sequence : (5' to 3'),Size,Epsilon, MW, Tubes/OD,nmoles,Volume,Concentration,ug/ul,Tm,Extraname,Plate Name,SPECIAL,Qty ug,Dimer,2ndry pattern,GC%,ul for 100uM\n"
    >>> fd.readline()
    'VC00021,8009959041-000010,STANDARD[0.0500 UMO],,HPLC,,[000010]B|4f-target-Cy3,AGCTTGCAAATTCCACCCGTGTTTAATAAACACCTAGG[Cy3],38,,12216.8,1 Tubes /  23.6,64.288,,,,77.2,-,-,-,785.388,No,Moderate,41.026,642.88\n'
    >>> fd.seek(505) # Seek back to start position.
    """
    if delimiters is None:
        delimiters = (",", "\t", ";")
    # Hmm... as soon as you invoke fd.next (via e.g. an iteration),
    # the file is parsed through to end of file.
    # Ahh... buffering...!
    pos = fd.tell()
    row = fd.readline()
    nskiprows = 0
    while row:
        #print "nskiprows,pos,fd.tell() = (%s, %s, %s), row is: '%s'" % (nskiprows, pos, fd.tell(), row)
        if any(delimiter in row for delimiter in delimiters):
            fd.seek(pos)
            #print "Returning nskiprows,pos = (%s, %s)" % (nskiprows, pos)
            return (nskiprows, pos)
        pos = fd.tell()
        row = fd.readline()
        nskiprows += 1



def gen_csv_data(inputfilehandle, returntype='generator'):
    """
    Takes an input filehandle and returns a generator
    with rows represented as dicts.
    """
    # First do some sniffing (I expect input smmc file to have headers!)
    skipinfo = getcsvskiprows(inputfilehandle)
    if skipinfo is None:
        logger.debug("No headerrow found for file: %s", inputfilehandle)
        return ( i for i in tuple() )
    nskiprows, fpos = skipinfo
    snif = csv.Sniffer()
    sample = inputfilehandle.read(3*1024).split('\n\n')[0]
    logger.debug("sniffer sample data: %s", sample)
    csvdialect = snif.sniff(sample) # The read _must_ encompass a full first line.
    csvdialect.lineterminator = '\n' # Ensure correct line terminator (\r\n is just silly...)
    #logger.debug("Using headerrow: %s\ncsvdialect: %s", headerrow, csvdialect)
    inputfilehandle.seek(fpos) # Reset file
    # Then, extract dataset:
    setreader = csv.DictReader(inputfilehandle, dialect=csvdialect)
    # Import data
    # Note: Dataset is a list of dicts.
    if returntype == 'list':
        return [row for row in setreader if len(row)>0]
    elif returntype == 'csvreader':
        return setreader
    else:
        return (row for row in setreader if len(row)>0)


def findFieldByHint(candidates, hints, scorebar=0.2, require=None):
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
        if require and require not in candidate:
            return 0
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
        scores = [ calculate_score(candidate.lower(), hint.lower()) for candidate in candidates ]
        #print "="
        scores_list = [cand+"({}) ({:.3f})".format(type(cand), score) for cand, score in zip(candidates, scores)]
        #print scores_list
        scores_str = ", ".join( scores_list )
        #print scores_str
        #print "--------"
        # do NOT attempt to use u"string" here, doesn't work?
        #logger.debug("Candidate scores for hint '%s': %s" , hint, scores_str)
        if max(scores) > scorebar:
            return candidates[scores.index(max(scores))]
        #for candidate in candidates:
        #    if hint in candidate.lower():
        #        return candidate
    # None of the hints were found in either of the options.
    return None

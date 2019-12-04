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
Brutally taken from the old epmotion_staplemixer.FileHelper object and
split into functions rather than having an unnessecary class helper.

This contains all functions relevant to (csv) files.

Functions specific to rackfiles (*.rack.csv) should be placed
in rackfileutils.py




"""

import os
import csv
import re

# imported as needed:
#import xlrd # Support for reading both old xls and new xlsx files!
# xlrd homepage: www.python-excel.org, github.com/python-excel/xlrd
# xlrd is the oldest excel module; new release Apr 2013.
# Other excel modules:
# xlwt - for writing old binary MS Excel 97/2000/XP/2003 XLS files
# XlsxWriter - advanced xlsx writer, but cannot read files.
# openpyxl - read/write of excel 2007 xlsx files.
# As of Jan 2014, both XlsxWriter and openpyxl are in active development
# with daily commits to the bitbucket/github repositories.
# https://bitbucket.org/ericgazoni/openpyxl/commits/all
# https://github.com/jmcnamara/XlsxWriter/commits/master
# https://github.com/python-excel/xlrd/commits/master



## Logging:
import logging
logger = logging.getLogger(__name__)
#logging.getLogger("__main__").setLevel(logging.DEBUG)
#logger.setLevel(logging.DEBUG)


try:
    import magic
    magic_available = True
    if hasattr(magic, 'MAGIC_MIME_TYPE'):
        magic_is_old = True
    else:
        magic_is_old = False
except ImportError:
    magic_available = False
    magicmime = None
    logger.info("Notice: magic module is not available; mimetypes will be based on file extensions. See http://pypi.python.org/pypi/python-magic/ for info on installing the filemagic python module.")
    import mimetypes


def getmimetype(filepath):
    """
    Returns the mime type of a file, using the best
    methods available on the current installation.

    Magic is currently disabled, since both the new python-magic
    and the old filemagic module yields 'application/msword' for .xls files!

    Note that the mimetype returned by mimetypes module is different, e.g.
        mimetypes.guess_type('excelfile.xls') --> 'application/vnd.ms-excel'
        mimetypes.guess_type('excelfile.xlsx') --> 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    However, the mimetypes module cannot get the mimetype of unknown file extensions.

    Conclusion: If you need to determine a if a file is a particular file type,
    it is probably better to simply look for the extension manually.
    >>> fnroot, ext = os.path.splitext(filepath)
    """
    if magic_available and False:
        if magic_is_old:
            with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
                if hasattr(filepath, 'read'):
                    # It is probably a file descriptor or buffer or something:
                    mimetype = m.id_buffer(filepath.read(500*1024)) # Make sure not to read too much.
                else:
                    mimetype = m.id_filename(filepath)
        else:
            #with magic.Magic(mime=True) as m: # Not recommended; https://github.com/ahupp/python-magic
            #    mimetype = m.from_file(filepath)
            # Uhh... the python-magic gives some really weird mime-types, e.g.
            # >>> magic.from_buffer("hej der")
            # Out[49]: 'ASCII text, with no line terminators'
            # "To identify with mime type, rather than a textual description, pass mime=True."
            if hasattr(filepath, 'read'):
                mimetype = magic.from_buffer(filepath.read(500*1024), mime=True)
            else:
                mimetype = magic.from_file(filepath, mime=True)
    else:
        # mimetypes.guess_type returns <mimetype>, <encoding>.
        # Only takes a url string, does not support reading buffers...
        # Actually, this seems to be more precise in many cases,
        # than magic (at least the old magic, which yields 'application/msword' for '*.xls' files!)
        if hasattr(filepath, 'name'):
            filepath = filepath.name
        mimetype, _ = mimetypes.guess_type(filepath, strict=False)
    return mimetype


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
        scores = [ calculate_score(candidate.lower(), hint.lower()) for candidate in candidates ]
        #print "="
        scores_list = [cand+"({}) ({:.3f})".format(type(cand), score) for cand, score in zip(candidates, scores)]
        #print scores_list
        scores_str = ", ".join( scores_list )
        #print scores_str
        #print "--------"
        # do NOT attempt to use u"string" here, doesn't work?
        logger.debug("Candidate scores for hint '%s': %s" , hint, scores_str)
        if max(scores) > 0.2:
            return candidates[scores.index(max(scores))]
        #for candidate in candidates:
        #    if hint in candidate.lower():
        #        return candidate
    # None of the hints were found in either of the options.
    return None


def removeFileExt(filename, extcandidates):
    """
    Takes a filename and a list of possible extensions and
    returns the actual filename without extension.
    (Not sure this is optimally implemented, look online for better solutions if required...)
    """
    for candidate in extcandidates:
        if candidate in filename:
            return filename[:len(filename)-len(candidate)]
    # If no extension was determined, just return fnroot:
    fnroot, ext = os.path.splitext(filename)
    return fnroot


def natural_sort(l):
    """
    Natural sorting algorithm,
    from http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
    """
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)



def gen_input_filehandles(filenames):
    """
    Generator.
    Returns a generator with file handles for input files:
    """
    # Made so it can easily be adapted to yield multiple handles in sequence:
    # logger.debug() # argh, the really anoying thing about using generators:
    # you cannot do introspection or print/log the values for debugging prior to using them.
    logger.debug("os.getcwd(): %s", os.getcwd())
    for csvfilename in filenames:
        with open(csvfilename, 'rU') as oligolistfile:
            yield oligolistfile


def gen_csv_data(inputfilehandle):
    """
    Takes an input filehandle and returns a generator
    with rows represented as dicts.
    """
    # First do some sniffing (I expect input smmc file to have headers!)
    snif = csv.Sniffer()
    csvdialect = snif.sniff(inputfilehandle.read(2048)) # The read _must_ encompass a full first line.
    #alternatively, select the separator character that is mentioned the most in the first row:
#                sep =  max([',','\t',';'], key=lambda x: myline.count(x))
    csvdialect.lineterminator = '\n' # Ensure correct line terminator (\r\n is just silly...)
    inputfilehandle.seek(0) # Reset file
    # Then, extract dataset:
    setreader = csv.DictReader(inputfilehandle, dialect=csvdialect)
    # Import data
    # Note: Dataset is a list of dicts.
    return (row for row in setreader if len(row)>0)


def gen_csv_datasets(input_filehandles):
    """
    Generator. Each generated value is it self a generator of rows (as dicts) from the csv files.
    Use as:
        for filedata in gen_csv_data():
            for row in filedata:
                row['field'] = new_value
    For each input filehandle, returns a csv-based data generator for that file,
    consisting of a list(generato) of dicts.
    """
    for oligolistfile in input_filehandles:
        yield (dataset for dataset in gen_csv_data(oligolistfile) )
    # alternatively, to avoid the for loop, do:
    # return ( (data for data in gen_csv_data(oligolistfile)) for oligolistfile in input_filehandles )


def gen_xls_data(fd):
    """
    Similar to gen_csv_data but produced from an excel file.
    Returns a generator of dicts.
    Read into memory before fd is closed.
    """
    # xlrd supports both old xls and new xlsx files :)
    from xlrd import open_workbook
    from mmap import mmap, ACCESS_READ
    #fmmap = mmap(f.fileno(),0,access=ACCESS_READ)
    wb = open_workbook( file_contents=mmap(fd.fileno(), 0, access=ACCESS_READ) )
    ws = wb.sheets()[0]
    logger.info("Using worksheet: '%s'", ws.name)
    fieldheaders = ws.row_values(0)
    data = ( dict(list(zip(fieldheaders, ws.row_values(i)))) for i in range(1, ws.nrows) )
    return data












def writecsvdatasetstofiles(datasets, outputfn_fmt='output_24wp_{:02}.rack.csv', dialect=None):
    """
    Take a list/iterable of datasets and write the data to output files with filename format outputfn_fmt.
    """
    ## OLD:
    #Takes a list of tuples:
    #    (filename, data)
    #and write data to file with filename.
    #if filetups is None:
    #    filetups = ( (outputfn_fmt.format(i), data) \
    #                  for i, data in enumerate(gen_calculated_resuspend_datasets()) )
    for i, data in enumerate(datasets, 1):
        if data:
            filename = outputfn_fmt.format(i)
            with open(filename, 'wb') as filehandle:
                writecsvdata(filehandle, data, dialect)


def writecsvdata(filehandle, data, dialect=None):
    """
    Does the actual writing of a single data set to file.
    """
    if dialect is None:
        dialect = Csvdialect()
    firstrow = True
    for row in data:
        if firstrow:
            filehandle.write( dialect.delimiter.join(list(row.keys())))
        firstrow = False
        filehandle.write(dialect.newline+dialect.delimiter.join(str(val) for val in list(row.values())))


class Csvdialect(csv.excel_tab):
    """
    Used in place of csv.Dialect.
    """
    def __init__(self, *args, **kwargs):
        csv.excel_tab.__init__(self, *args, **kwargs)
        self.newline = '\n'
        self.delimiter = '\t'



#
#
#class FileHelper():
#    """
#    Remember, when you take a function and make it a method, you need to
#    remember that first self argument
#    """
#    #def findmostsimilar(self, designname, ext):
#    #    """ Currently NOT used..."""
#    #    #print "findmostsimilar for design: " + designname + " and extension " + ext
#    #    # Using glob.glob for readability:
#    #    #dirlist = [fname for fname in os.listdir(os.getcwd()) if fname[len(fname)-len(ext):] == ext] # filter
#    #    dirlistglob = glob.glob("*"+ext)
#    #    print "Comparing dirlist and dirlistglob:"
#    #    print dirlist
#    #    print dirlistglob
#    #    # Need to make sure that we have candidates. dirlist might be empty.
#    #    if not dirlist:
#    #        print "WARNING: No map-file candidates were found with extension %s" % ext
#    #        # just return None and it will be dealt with properly. Do not return "".
#    #        return None
#    #    best_score = 0
#    #    for fname in dirlist:
#    #        v = calc_score(designname, fname)
#    #        if v > best_score:
#    #            best_score = v
#    #            best_file = fname
#    #    return best_file

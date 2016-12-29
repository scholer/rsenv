#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Sun May 19 2013

@author: scholer

Includes code for manupilation of cadnano files and derived files, including staple lists, etc.

See also:
 - OligoManager2 module: oligomanager.tools.file_transformation


"""


""" ----------------------------------------------------
Parsing, handling and manipulating set file information
---------------------------------------------------- """

#import sys
import logging
logger = logging.getLogger(__name__)

#import rsseq
from rsenv.seq.sequtil import dnacomplement


def filterfilebycolor(staplesetfilepath, outputfilename=None, filtercolor=None, desc=None, writeToFile=True,
    appendToFile=False, writeheader=False, replacecolor=None, replacemodulename=None, sep=None):
    """
    Simple function that filters lines in a staplesetfile.
    """
    headers = None
    nomodulenameflag = False
    if writeToFile:
        fileflags = 'a' if appendToFile else 'w'
        if outputfilename is None:
            outputfilename = staplesetfilepath+".filtered"
    else:
        raise NotImplementedError("filterfilebycolor() has not implemented writeToFile=False yet.")
#        import stringio.StringIO as StringIO
#        newfile = StringIO()

    with open(staplesetfilepath) as inputfile, open(outputfilename, fileflags) as outputfile:
        lines = (line.strip() for line in inputfile if line.strip())
        testline = next(lines)
        # If there are more tabs in the first line than there is commas, then use tabs as separator.
        sep = '\t' if (len(testline.split('\t')) > len(testline.split(','))) else ','
        headers = testline.split(sep)
        if replacemodulename and "Modulename" not in headers:
            headers.append("Modulename")
        if writeheader:
            outputfile.write(sep.join(headers)+"\n")
        for line in lines:
            row = line.split(sep)
            rowdict = dict(list(zip(headers, row)))
            if rowdict["Color"] == filtercolor or rowdict["Color"] in filtercolor:
                if replacecolor:
                    rowdict["Color"] = replacecolor
                if replacemodulename:
                    rowdict["Modulename"] = replacemodulename
                outputfile.write(sep.join(rowdict[header] for header in headers)+'\n')


class RsFileObject(object):
    def __init__(self, fileobj, fileflags='r'):
        if isinstance(fileobj, str):
            self._filename = fileobj
            self.fileobj = open(fileobj, fileflags)
        else:
            self._filename = None
            if fileobj:
                self.fileobj = fileobj
            else:
                from io import StringIO
                self.fileobj = StringIO()
    def close(self):
        if self._filename:
            self.fileobj.close()
    def write(self, data):
        self.fileobj.write(data)
    def writeline(self, data):
        self.fileobj.write(data+'\n')


def append_sequence_to_staps(
        staplesetfilepath, appendSeq, filtercolor=None, appendToFivePrime=False,
        isComplement=False, desc="", verbose=0, outsep='\t', writeToFile=True, appendToFile=False,
        newfilename=None, lnstrformat=None, writeonlyfiltered=True, keepOrgSequence=False,
        writeheader=True, replacecolor=False, replacemodulename=False):
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
        writeToFile : Write to this file (like object).
                    If writeToFile is a string, it is interpreted as a filename/path.
                    If writeToFile is False, will write all lines to a StringIO object which is returned.
                    Otherwise, writeToFile is assumed to be a writable file.
                    Use writeToFile=sys.stdout to print to standard out.
                    Default is True.
        appendToFivePrime: If true, append appendSeq to 5' end of input sequence. Default is False (appends to 3').
        newfilename : name of output file. If not given, output will be inputfilename+'.append'
        lnstrformat : format of the lines written by this file.
                      lnstrformat magic words are: "orderlist", "combined":
                        "combined" : Combine old fields with new (if any), keeping the order intact.
                        "orderlist": Creates a file that is ready for order.
                      if not set, lnstrformat will default to "combined".
        writeonlyfiltered : If true (default) only write lines that passes the filtercolor filter.
                            If set to false, all lines will be written.
        keepOrgSequence : If set, will add a field called OriginalSequence and put original sequence here.
        writeheader : If True, will write the header. (Should be set to false if appendToFile is True.
        replacecolor: If set, will replace input color with another color.
        replacemodulename: If set, will replace 'Modulename'.
    """
    orderlistformat = "{Description}:{Start}\t{Sequence}\t{Length}"
    if lnstrformat is None:
        # "combined" is defined later when the header has been parsed from the input file.
        #print "lnstrformat defaulted to 'combined'."
        lnstrformat = "combined"
    elif lnstrformat == "orderlist":
        if desc:
            lnstrformat = orderlistformat # desc,Start, seq, len(seq)
        else:
            lnstrformat = "{Sequence}"
    if isComplement:
        appendSeq = dnacomplement(appendSeq).upper()
        #print "Appending seq: " + appendSeq
    if isinstance(writeToFile, str):
        fileflags = 'a' if appendToFile else 'w'
        newfile = open(writeToFile, fileflags)
    elif writeToFile:
        newfile = writeToFile
    else:
        from io import StringIO    # python2, python3 is stringio.StringIO
        newfile = StringIO()
    with open(staplesetfilepath, 'rb') as fp:
        # simple test for whether to use comma or tab as separator:
        lines = (line.strip() for line in fp if line.strip())
        testline = next(lines)
        # If there are more tabs in the first line than there is commas, then use tabs as separator.
        sep = '\t' if (len(testline.split('\t')) > len(testline.split(','))) else ','
        if outsep is None:
            outsep = sep
        header = testline.split(sep)
        if desc:
            header.append('Description')
        if keepOrgSequence:
            header.append('OriginalSequence')
        if lnstrformat == "combined":
            # Combine the existing format with new fields (e.g. description, etc.
            lnstrformat = outsep.join("{0}".format("{"+field+"}") for field in header)
        #print "Line format is: {}".format(lnstrformat)
        if writeheader:
            if lnstrformat == orderlistformat:
                newfile.write(orderlistformat.replace("{", "").replace("}", "")+'\n')
            else:
                newfile.write(outsep.join(header)+'\n')
        # Header map: maps a header string to column index
        #hm = {v: i for i, v in enumerate(header)}
        rows = (line.split(sep) for line in lines)
        # You may want to capture to list instead of generator and close the file here...
        for row in rows:
            rowdict = dict(list(zip(header, row)))
            if keepOrgSequence:
                rowdict['OriginalSequence'] = rowdict['Sequence']
            if filtercolor is None or (len(row)>1 and (rowdict['Color'] == filtercolor or rowdict['Color'] in filtercolor)) :
                rowdict['Description'] = desc # if desc is None, then lnstrformat will NOT include Description.
                seq = rowdict['Sequence']
                seq = "".join([appendSeq, seq]) if appendToFivePrime else "".join([seq, appendSeq])
                rowdict['Sequence'] = seq
                if replacecolor:
                    rowdict['Color'] = replacecolor
                if replacemodulename:
                    rowdict['Modulename'] = replacemodulename
                rowdict['Length'] = len(seq)
                ln = lnstrformat.format(**rowdict)
                if verbose:
                    print(ln)
                newfile.write(ln+"\n")
            elif not writeonlyfiltered:
                # Write line even if it does not match filter...:
                rowdict['Description'] = ''
                ln = lnstrformat.format(**rowdict)
                newfile.write(ln+"\n")
#                rowdict['Description'] = rowdict.get('Description', "")
                #newfile.write(outsep.join(row+[""]*(len(header)-len(row)))+'\n')   # uh, what?

    if isinstance(writeToFile, str):
        newfile.close()
    else:
        return newfile

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
Created on Sun May 19 2013

@author: scholer

Includes code for manupilation of cadnano files and derived files, including staple lists, etc.

See also:
 - Dropbox/Dev/Projects/OligoManager2/oligomanager/tools/file_transformation


"""


""" ----------------------------------------------------
Parsing, handling and manipulating set file information 
---------------------------------------------------- """
#def filterbycolor(line, 


def filterfilebycolor(staplesetfilepath, outputfilename=None, filtercolor=None, desc=None, writeToFile=True, 
    appendToFile=False, writeheader=False, replacecolor=None, replacemodulename=None, sep=None):
    """
    Simple function that filters lines in a staplesetfile.
    """
    headers = None
    nomodulenameflag = False
    if writeToFile:
        if appendToFile: fileflags = 'a'
        else: fileflags = 'w'
        if outputfilename is None:
            outputfilename = staplesetfilepath+".filtered"
    else:
        raise NotImplementedError("filterfilebycolor() has not implemented writeToFile=False yet.")
#        import stringio.StringIO as StringIO
#        newfile = StringIO()

    with open(staplesetfilepath) as inputfile, open(outputfile, fileflags) as outputfile:
        for line in inputfile:
            if sep is None:
                sep = "\t" if "\t" in line else "," if "," in line else ";"
            row = line.strip().split(sep)
            if headers is None:
                headers = row
                if replacemodulename and "Modulename" not in headers:
                    headers.append("Modulename")
                if writeheader:
                    outputfile.write(sep.join(headers)+"\n")
            rowdict = dict(zip(header, row))
            if rowdict["Color"] == filtercolor or rowdict["Color"] in filtercolor:
                if replacecolor:
                    rowdict["Color"] = replacecolor
                if replacemodulename:
                    rowdict["Modulename"] = replacemodulename
                outputfile.write(sep.join(rowdict(header) for header in headers)+'\n')



def appendSequenceToStaps(staplesetfilepath, appendSeq, filtercolor=None, appendToFivePrime=False,
    isComplement=False, desc="", verbose=0, outsep='\t', writeToFile=True, appendToFile=False,
    newfilename=None,lnstrformat=None, writeonlyfiltered=True, keepOrgSequence=False,
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
        writeToFile : If false, will write all lines to a StringIO object which is returned. Default is True.
        appendToFivePrime: If true, append appendSeq to 5' end of input sequence. Default is False (appends to 3').
        newfilename : name of output file. If not given, output will be inputfilename+'.append'
        lnstrformat : format of the lines written by this file. 
                      lnstrformat magic words are: "orderlist", "combined".
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
        print "lnstrformat defaulted to 'combined'."
        lnstrformat = "combined"
    elif lnstrformat == "orderlist":
        if desc:
            lnstrformat = orderlistformat # desc,Start, seq, len(seq)
        else:
            lnstrformat = "{Sequence}"
    if isComplement:
        appendSeq = dnacomplement(appendSeq).upper()
        print "Appending seq: " + appendSeq
    if writeToFile:
        if appendToFile: fileflags = 'a'
        else: fileflags = 'w'
        if newfilename is None:
            newfilename=staplesetfilepath+'.append'
        newfile = open(newfilename, fileflags)
    else:
        import stringio.StringIO as StringIO
        newfile = StringIO()
    with open(staplesetfilepath,'rb') as fp:
        # simple test for whether to use comma or tab as separator:
        testline = fp.readline().strip()
        # If there are more tabs in the first line than there is commas, then use tabs as separator.
        sep = '\t' if (len(testline.split('\t')) > len(testline.split(','))) else ','
        if outsep is None: outsep = sep
        header = testline.split(sep)
        if desc:
            header.append('Description')
        if keepOrgSequence:
            header.append('OriginalSequence')
        if lnstrformat == "combined":
            # Combine the existing format with new fields (e.g. description, etc.
            lnstrformat = outsep.join("{0}".format("{"+field+"}") for field in header)
        print "Line format is: {}".format(lnstrformat)
        if writeheader:
            if lnstrformat == orderlistformat:
                newfile.write(orderlistformat.replace("{","").replace("}","")+'\n')
            else:
                newfile.write(outsep.join(header)+'\n')
        # Header map: maps a header string to column index
        hm = dict([(v,i) for i,v in enumerate(header)])
        #fp.seek(0) # I have only read the header, so no reason to seek back.
        for line in fp:
            row = line.strip().split(sep)
            rowdict = dict(zip(header, row))
            if filtercolor is None or (len(row)>1 and (rowdict['Color'] == filtercolor or rowdict['Color'] in filtercolor)) :
                rowdict['Description'] = desc # if desc is None, then lnstrformat will NOT include Description.
                seq = rowdict['Sequence']
                if appendToFivePrime:  
                    seq = "".join([appendSeq, seq])
                else:
                    seq = "".join([seq, appendSeq])
                if keepOrgSequence:
                    rowdict['OriginalSequence'] = rowdict['Sequence']
                rowdict['Sequence'] = seq
                if replacecolor:
                    rowdict['Color'] = replacecolor
                if replacemodulename:
                    rowdict['Modulename'] = replacemodulename
                rowdict['Length'] = len(seq)
                ln = lnstrformat.format(**rowdict)
                if verbose: print ln
                newfile.write(ln+"\n")
            elif not writeonlyfiltered:
#                rowdict['Description'] = rowdict.get('Description', "")
                newfile.write(outsep.join(row+[""]*(len(header)-len(row)))+'\n')
    if writeToFile:
        newfile.close()
    else:
        return newfile





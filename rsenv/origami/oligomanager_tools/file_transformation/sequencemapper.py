#!/usr/bin/python
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
Created on Thu Aug  4 10:45:45 2011

@author: scholer
"""

### MAPPING pieces of undefined sequence to a proper sequence.
### This is defined as <number of undefined bases> --> 'A proper sequence'
### The length of undefined bases does not have to correspond to the replaced sequence.
### MOST LOGIC FROM bizOm_Oligos.mapSeq(seq, mapchar, map)

import re, csv
import sys, os, binascii
import logging
logger = logging.getLogger(__name__)


class OligosetFileSequenceMapper:


    def __init__(self, oligosetfilename, seqmapfilename, initialDict=dict(), mapchar='\?', verboselevel=3):
        """ Provide seqmapfilename=None in order to not read a seqmap from file
        but rather just use the map given in initialDict."""
        self.AllOK = None
        self.Oligosetfilename = oligosetfilename
        self.Seqmapfilename = seqmapfilename
        self.Mapchar = mapchar
        self.Map = initialDict
        self.UsedMapKeys = set() # I'd like to save the used keys for later reference.
        self.Verboselevel = verboselevel # Set this to -1 to suppress all log messages (e.g. if you want to use stdout for outputting the file)

        # First, load the oligosetfile into memory
        if oligosetfilename:
            with open(oligosetfilename, 'rU') as oligosetfile:
                snif = csv.Sniffer()
                self.InputHasHeader = snif.has_header(oligosetfile.read(1024))
                oligosetfile.seek(0)
                self.CsvDialect = snif.sniff(oligosetfile.read(1024))
                # csv sniffer does a very poor job locating the real lineterminator,
                # e.g. even though the input file has newline only (0x0A),
                # sniffer reports \r\n (0x0D,0x0A) as the line terminator.
                # I'll thus specify it manually myself. Also remember to write files in binary mode.
                self.CsvDialect.lineterminator = '\n'
                oligosetfile.seek(0)
                # Important lesson: You DictReader has several more arguments, so you must define dialect=<dialect> for it to work.
                setreader = csv.DictReader(oligosetfile, dialect=self.CsvDialect)
                # a list of dicts
                self.FileFields = setreader.fieldnames
    #            print "self.CsvDialect.delimiter:" + binascii.hexlify(self.CsvDialect.delimiter) + "<--"
    #            print "self.CsvDialect.lineterminator:" + binascii.hexlify(self.CsvDialect.lineterminator) + "<--"
    #            print "self.CsvDialect.doublequote:" + str(self.CsvDialect.doublequote) + "<--"
    #            print "self.CsvDialect.escapechar:" + str(self.CsvDialect.escapechar) + "<--"
    #            print "self.CsvDialect.quotechar:" + str(self.CsvDialect.quotechar) + "<--"
    #            print "self.CsvDialect.quoting:" + str(self.CsvDialect.quoting) + "<--"
    #            print setreader.fieldnames

                self.Dataset = [row for row in setreader if len(row)>0]
                if self.Verboselevel > 6:
                    print "Dataset from file: " + oligosetfilename
                    print self.Dataset

        # Load the sequencemap from file (if a file is given)
        if seqmapfilename is not None:
            # TODO: Change this, so that it just reads the file like it is done elsewhere,
            # i.e. read per line, and split on whitespace (except if line starts with '#')
            with open(seqmapfilename, 'rU') as seqmapfile:
                try:
                    #mapreader = csv.reader(seqmapfile, delimiter='\t')
                    filerows = (line.strip().split() for line in seqmapfile if line and line[0] != '#')
                    seqmap = {int(row[0]) : row[1] for row in filerows} # Make sure you read *before* closing the file.
                except IOError as e:
                    print e
                    return
                else:
                    #seqmap = {int(row[0]) : row[1] for row in mapreader if len(row)>1}
                    logger.debug("Map loaded from file '%s': %s", seqmapfilename, seqmap)
                    self.Map.update(seqmap)
        else:
            # If no seqmapfilename is specified... well, just use the initialDict map given in init...
            pass

        # Find 'seq' header in the dataset:
        self.SeqDataKey = None
        for key in self.Dataset[0].keys():
            # I really do assume keys to be strings...
            if 'seq' in key.lower():
                self.SeqDataKey = key
                break
        if self.SeqDataKey is None:
            print "Error, could not find any columns in the oligoset file containing 'seq'."
            self.AllOK = False # Flag not to continue...

    def transformData(self, mapchar=None):
        """Perform transformation of each sequence."""

        self.UsedMapKeys = set() # reset the set.

        if mapchar is None:
            if self.Mapchar is None:
                mapchar='\?'
            else:
                mapchar = self.Mapchar
        if self.Verboselevel > 1:
            print "OligosetFileSequenceMapper: Transforming data..."
        for row in self.Dataset:
            if self.Verboselevel == 5:
                print "old sequence:     " + row[self.SeqDataKey]
            row[self.SeqDataKey] = self.mapSeq(row[self.SeqDataKey], mapchar, self.Map)
            if self.Verboselevel == 5:
                print "-- transformed -->"  + row[self.SeqDataKey]

        if self.Verboselevel > 1:
            print "Data transformation completed."
            print "Used sequence maps:"
            usedKeys = list(self.UsedMapKeys) # Produce a list from the set.
            usedKeys.sort() # Sort the list

            for key in usedKeys:
                # ey.zfill(3), ": ",
                print "".join(["%03d" % key, ": ", self.Mapchar.replace("\\", "")*key, " --> ", self.Map[key] ])


    def writeNewData(self, newfilename=None):

        if self.Verboselevel > 2:
            print "\nWriting new data:"

        if newfilename is None:
            newfilename = self.Oligosetfilename + ".sm"
            if self.Verboselevel > 2:
                print "writeNewData(): No newfilename given, so using : " + newfilename

        # Always open as binary ('wb') when dealing with csv files.
        with open(newfilename, 'wb') as f:
            # Write file. The default in caDNAno is to
            dw = csv.DictWriter(f, self.FileFields, dialect=self.CsvDialect) #lineterminator='\n', delimiter='\t')
            if hasattr(dw, 'writeheader'):
                # Requires python 2.7+
                dw.writeheader()
            else:
                f.write("\t".join(self.FileFields) + "\n") # Just as quick...

            dw.writerows(self.Dataset)

        if self.Verboselevel > 2:
            print "writeNewData(): Done!"


    def mapSeq(self, seq, mapchar=None, map=None):
        """ Recursively find longest stretches of <mapchar> in seq and replace using the given map. """
        # Store the current method name in case it is changed:
        _current_fun = self.mapSeq

        if mapchar is None:
            print "mapSeq() Warning: no mapchar provided, using '\?' !!"
            mapchar = '\?'
        if map is None:
            print "mapSeq() Warning: no map provided, using '?->T' !!"
            map = dict()
            for i in range(20): map[i]='T'*i

        match = re.search(mapchar+'+', seq)
        if match is None:
            return seq
        else:
            try:
                ret = "".join([
                    seq[0:match.start()], # Part before match
                    map[len(match.group())], # the match, mapped to specified sequence
                    _current_fun(seq[match.end():], mapchar, map) # the rest of the sequence
                    ])
                self.UsedMapKeys.add(len(match.group())) # Add the match-length to the list of used keys in the map.
            except KeyError:
                print "Unknownbase-mapping :: mapSeq() ERROR: Could not map unumber ", len(match.group())
                print "  sequence: ", seq
                print ""
                ret = "".join([
                    seq[0:match.start()], # Part before match
                    '?'*len(match.group()), # the match, which could not be mapped...
                    _current_fun(seq[match.end():], mapchar, map) # the rest of the sequence
                    ])
            return ret

def mapseq(seq, mapchar, seqmap, usedkeyset=None):
    """
    Maps stretches of <mapchar> character in <seq> using the map in <seqmap>.
    <seqmap> should be a dict, where keys correspond to the lengths of the mapchar stretches,
    and the values are the replacement sequence (str).
    """
    if usedkeyset is None:
        usedkeyset = set()
    print "mapchar: ", mapchar
    match = re.search(mapchar+'+', seq)
    if match is None:
        return seq
    else:
        try:
            ret = "".join([
                seq[0:match.start()], # Part before match
                seqmap[len(match.group())], # the match, mapped to specified sequence
                mapseq(seq[match.end():], mapchar, seqmap) # the rest of the sequence
                ])
            usedkeyset.add(len(match.group())) # Add the match-length to the list of used keys in the map.
        except KeyError:
            print "Unknownbase-mapping :: mapSeq() ERROR: Could not map unumber ", len(match.group())
            print "  sequence: ", seq
            print ""
            ret = "".join([
                seq[0:match.start()], # Part before match
                '?'*len(match.group()), # the match, which could not be mapped...
                mapseq(seq[match.end():], mapchar, seqmap) # the rest of the sequence
                ])
        return ret



if __name__ == "__main__":

    import argparse
    argparser = argparse.ArgumentParser(description='Find stretches of undefined bases and replace with proper sequence using a sequence map from a file.')
    argparser.add_argument('oligosetfilename', help="Name of the file which contains the oligos which need to have their sequences transformed." )
    argparser.add_argument('-m', '--seqmapfilename', required=True, help="Name of the file that contains the sequence map. This must be a tab-separated file in the format '<N>    <sequence>' where N is the number of '?' characters and sequence is the sequence to replace with. If no seqmapfile is given, ? will be mapped to Ts. This can also just be done with sed: sed 's/\?/T/g' < input > output")
    argparser.add_argument('--include-default-T-mapping', '-T', action='store_true', help="Add this to make the first 1-100 entries be filled with T-linkers. A fine starting point that let's you focus your map file on the complex cases.")
    argparser.add_argument('--print-all-transformations', action='store_true', help="Explicitly print all sequence transformations.")
    argparser.add_argument('--mapchar', default='\?', help="Specify the character that marks undefined bases. Special characters such as ? must be escaped. Default is '\?'.")
    argparser.add_argument('--stdout', action='store_true', help="Print output to standard out instead of a file.")
    argparser.add_argument('--writefile', default=None, help="Specify a filename to use for the output. If none is specified, '.seqmapped' is appended to the given input file name.")
    argparser.add_argument('--verboselevel', default=3, type=int, help="Specify how verbose you want to run the program.")

    args = argparser.parse_args()

    if args.stdout:
        # If using stdout, we need to supress all other prints completely.
        verboselevel = -1
    elif args.print_all_transformations:
        verboselevel = 5
    else:
        verboselevel = args.verboselevel

    if args.include_default_T_mapping or args.seqmapfilename is None:
        initMap = dict([(i, 'T'*i) for i in range(200)])
    else:
        initMap = dict()


    maptransformer = OligosetFileSequenceMapper(args.oligosetfilename,
                                                args.seqmapfilename,
                                                initMap, args.mapchar,
                                                verboselevel=verboselevel)

    maptransformer.transformData()

    maptransformer.writeNewData(args.writefile)

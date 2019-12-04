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
### Based on sequencemapper.py

import csv


class OligosetFileColorMapper:

    def __init__(self, oligosetfilename, colormapfilename, initialDict=None, verboselevel=3):
        #
        self.AllOK = None
        self.Oligosetfilename = oligosetfilename
        self.Colormapfilename = colormapfilename
        self.ModuleclassFieldname = 'Modulename'
        self.Map = initialDict if initialDict is not None else {}
        self.MapOrder = None
        self.UsedMapKeys = set() # I'd like to save the used keys for later reference.
        self.Verboselevel = verboselevel  # Set this to -1 to suppress all log messages

        # First, load the oligosetfile into memory
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
            # Important lesson: The DictReader has several more arguments, so you must define dialect=<dialect> for it to work.
            setreader = csv.DictReader(oligosetfile, dialect=self.CsvDialect)
            self.FileFields = setreader.fieldnames
            self.Dataset = [row for row in setreader if len(row)>0]
            if self.Verboselevel > 6:
                print(("Dataset from file: " + oligosetfilename))
                print((self.Dataset))

        # Load the modulecolormap from file
        with open(colormapfilename, 'rU') as colormapfile:
            # New version, kan manage mix cases of tabs and spaces, convenient when receiving ill-formatted colormap from untrained people.
            cmlines = [line.split(None,2) for line in colormapfile if len(line.split(None,2))>1 and line.split(None,2)[0][0]=="#" ]
            self.MapOrder = [row[0].lower() for row in cmlines]
            colormap = dict([(row[0].lower(), row[1]) for row in cmlines])
            # Map should be tab-separated text file with <color>    <module-class>
            #mapreader = csv.reader(colormapfile, delimiter='\t')
            #colormap = dict([(row[0],row[1]) for row in mapreader if len(row)>1])
            if self.Verboselevel > 5:
                print(("\nMap from file: " + colormapfilename))
                print(colormap)
            self.Map.update(colormap)

        # Find 'seq' header in the dataset:
        self.ColorDataKey = None
        for key in list(self.Dataset[0].keys()):
            # I really do assume keys to be strings...
            if 'color' in key.lower():
                self.ColorDataKey = key
                break
        if self.ColorDataKey is None:
            print("Error, could not find any columns in the oligoset file containing 'color'.")
            self.AllOK = False # Flag not to continue...

    def mapColorsToModules(self):
        """ Perform transformation of each sequence: """
        # Recent changes: I am now keeping track of all entries in colormap instead of only the entries being used.
        # --This is simpler, and print in same order as the colormap file.
        moduleStapleCount = dict([(color, 0) for color in self.MapOrder])
        if self.Verboselevel > 1:
            print("Mapping color to module in dataset...")

        for row in self.Dataset:
            try:
                row[self.ModuleclassFieldname] = self.Map[row[self.ColorDataKey]]
                moduleStapleCount[row[self.ColorDataKey]] += 1
            except KeyError:
                start = row["Start"] if "Start" in self.FileFields else "line\n--->" + "\t".join(row[field] for field in self.FileFields)
                print(("mapColorsToModules(): WARNING! Color '{0}' not in map, staple at {1}".format(row[self.ColorDataKey], start)))

        if self.ModuleclassFieldname not in self.FileFields:
            self.FileFields.append(self.ModuleclassFieldname)

        if self.Verboselevel > 1:
            print("Data transformation completed.")
            print("Color/module stats:")
            for color in self.MapOrder:
                print(("{0} --> {1} ({2} staples)".format(color, self.Map[color], moduleStapleCount[color])))
            # sorting using sorted: function specified by key is applied to all elements before sorting.
            # usedKeys = sorted(self.UsedMapKeys, key=lambda k:self.Map[k])

    def incrementDict(self, mydict, key, value=1, how='integer-add'):
        """
        Edit: This is pretty obsolte and obfuscating. Use the dict.get() to avoid getting key errors.
        """
        mydict[key] = value + mydict.get(key, 0)
        """
        PS: If you really want, you can override the __missing__ function of dict via subclassing,
        and specify your own default behaviour when dicts are queried with non-existent keys,
        c.f. http://stackoverflow.com/questions/101268/hidden-features-of-python#112286
        """

    def writeNewData(self, newfilename=None,fieldsep=None):
        # Write the current content of self.Dataset (hopefully updated by mapColorsToModules first)

        if fieldsep:
            self.CsvDialect.delimiter = fieldsep

        if self.Verboselevel > 3:
            print("\nWriting new data...")

        if newfilename is None:
            newfilename = self.Oligosetfilename + ".mc"
            if self.Verboselevel > 2:
                print(("writeNewData(): No newfilename given, so using : " + newfilename))

        # Always open as binary ('wb') when dealing with csv files.
        with open(newfilename, 'wb') as f:
            # Write file. The default in caDNAno is to
            dw = csv.DictWriter(f, self.FileFields, dialect=self.CsvDialect) #lineterminator='\n', delimiter='\t')
            if hasattr(dw, 'writeheader'):
                # Requires python 2.7+
                dw.writeheader()
            else:
                f.write(self.CsvDialect.delimiter.join(self.FileFields) + "\n") # Just as quick...

            dw.writerows(self.Dataset)

        if self.Verboselevel > 2:
            print("writeNewData(): Done!")


if __name__ == "__main__":

    import argparse
    argparser = argparse.ArgumentParser(description='caDNAno has no way of specifying module names in design files, only colors. This script uses a secondary color->module file to add entries to the oligo-list file.')
    argparser.add_argument('oligosetfilename', help="Name of the oligo-list file." )
    argparser.add_argument('-m', '--colormapfilename', required=True, help="Name of the file containing the map. This should be tab-separated with <color>   <module-class>.")
    argparser.add_argument('--stdout', action='store_true', help="Print output to standard out instead of a file.")
    argparser.add_argument('--writefile', default=None, help="Specify a filename to use for the output. If none is specified, '.mc' is appended to the given input file name.")
    argparser.add_argument('--verboselevel', default=3, type=int, help="Specify how verbose you want to run the program.")

    args = argparser.parse_args()

    if args.stdout:
        # If using stdout, we need to supress all other prints completely.
        verboselevel = -1
    else:
        verboselevel = args.verboselevel

    maptransformer = OligosetFileColorMapper(args.oligosetfilename,
                                            args.colormapfilename,
                                            verboselevel=verboselevel)

    maptransformer.mapColorsToModules()

    maptransformer.writeNewData(args.writefile)

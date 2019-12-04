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
This script tries to guess the proper filenames of sequence- and module-color maps.
You might want to adjust the calc_score method to fit your own particular use-case.
(Currently, it compares the first part before the file extension, all of which must
be included in the designfilename for it to be considered.)

Created on Mon Aug  8 17:45:12 2011

@author: scholer
"""


import argparse
import os
from sequencemapper import OligosetFileSequenceMapper
from modulecolormapper import OligosetFileColorMapper

#from pprint import pprint
#from StringCompareLimit import StringCompareLimit
#
#
#def calc_score_old(design, candidate):
#    # Compares two strings for similarity and returns a score...
#    # Brug limit til at kontrollere hvad den mindst accepterede similaritet skal være. (oprindeligt brugt til at optimere compare algoritmen)
#    # Bør sættes lavt, da vi kan have en meget ringe similaritet... Fx bør Box.seqmap bruges for alle Box.LockedD_B.Mar11-aug-foo-bar design...
#    # File extension filtret alene bør være nok...
#    strcomp = StringCompareLimit(str1, str2, limit=0.2)
#    return strcomp.calculate()

def calc_score(design, candidate):
    """ Calculates a score for how much <candidate> is similar to <design>. """
    # Uhm, I just figured: If I consider a filename like Box.LockedD_B.Mar11-aug-foo-bar.colormap
    # and I have two *.colormap in the directory: Box.LockedD_B.Mar11-old.colormap and Box.LockedD_B.colormap,
    # I'd probably want to use the Box.LockedDB.colormap file, even though the other have a more similar filename.
    # Conclusion: Only compare the first part and ignore the rest.
    mapname = candidate.rsplit('.', 1) # Split string once by the rightmost '.'
    if mapname[0] in design:
        #print "calc_score for design: " + design + " vs " + candidate + ": " + str(len(mapname[0]))
        return len(mapname[0])


def findmostsimilar(designname, ext):
    """
    Returns filename of another file in the current directory
    with extension <ext> and a filename that is the most similar to <designname>.
    """
    #print "findmostsimilar for design: " + designname + " and extension " + ext
    dirlist = [fname for fname in os.listdir(os.getcwd()) if fname[len(fname)-len(ext):] == ext] # filter
    # Need to make sure that we have candidates. dirlist might be empty.
    if not dirlist:
        print "WARNING: No map-file candidates were found with extension %s" % ext
        # just return None and it will be dealt with properly. Do not return "".
        return None
    best_score = 0
    best_file = None
    for fname in dirlist:
        v = calc_score(designname, fname)
        if v > best_score:
            best_score = v
            best_file = fname
    return best_file


if __name__ == "__main__":

    desc = "Performs sequence and module-color mapping using mapfiles ending with \
    '.seqmap' and '.colormap'. To use this, you need to produce these two files. \
    The .seqmap file format is:    <N><tab><Sequence>   \
    where N is number of ???, then a tab, then the sequence to map to, e.g.\n\
         4\tAAAGGGCTTTC..... \n\n\
    The .colormap file format is:\n<color><tab><name><tab><color description (convenience)>\n\
    E.g.      #03b6a2\tcol02\tCyan\n\
    (You can use color-hex.com to interpret color codes.)"
    argparser = argparse.ArgumentParser(description=desc)
    argparser.add_argument('oligosetfilename', help="Transform this file which list the oligos for an origami design, using sequencemapper and modulecolormapper.")
    argparser.add_argument('--mapchar', default=r'\?', help=r"Specify the character that marks undefined bases. Special characters such as ? must be escaped. Default is '\?'.")
    args = argparser.parse_args()

    filename = args.oligosetfilename
    mapfiles = [findmostsimilar(filename, ext) for ext in ['.seqmap', '.colormap'] ]

#    print "\nMapfiles returned:"
#    print mapfiles

    mapfile = mapfiles[0]
    if mapfile is None:
        print "Could not find any proper sequence maps."
        print "However, I will still run the list through the sequencemap, replacing up to 16 '" + args.mapchar + "' with the same number of 'T's."
        initialDict = dict([(i, 'T'*i) for i in range(20)])
    else:
        initialDict = dict([(i, 'T'*i) for i in range(8)])
        print "Using sequence map file: " + mapfile
        print "--Also replacing up to 6 {0} with the same number of 'T's.".format(args.mapchar)


    print "Using file: '{}'".format(filename)
    print "Current working directory: '{}'".format(os.getcwd())
    print "Does file exists? {}".format(os.path.exists(filename))
    fullpath = os.path.join(os.getcwd(), filename)
    print "Fullpath: '{}'".format(fullpath)
    print "Does cwd+filename exists? {}".format(os.path.exists(fullpath))

    maptransformer = OligosetFileSequenceMapper(filename,
                                                mapfile,
                                                initialDict=initialDict, # Per default, replace up to 8-mer T-linkers
                                                mapchar=args.mapchar,
                                                verboselevel=2)
    maptransformer.transformData()
    filename += ".smmc"
    print "Writing file: " + filename
    maptransformer.writeNewData(filename)

    mapfile = mapfiles[1]
    if mapfile is None:
        print "\nCould not find any proper module color maps, skipping."
    else:
        print "\nUsing module color map file: " + mapfile
        maptransformer = OligosetFileColorMapper(filename,
                                                mapfile,
                                                verboselevel=2)
        maptransformer.mapColorsToModules()
        #filename += ".mc"
        print "Writing file: " + filename
        maptransformer.writeNewData(filename)#,fieldsep='\t')

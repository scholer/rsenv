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


# About comparing e.g. module oligos:
# You can compare oligos on many different levels, going from just do a simple
# "added and removed" elements in a set of strings vs aligning the strings and
# finding actual changes, you can compare other changes like revision name, (well, probably doesn't make that much sense)
# Finally, you can compare one set against many existing (instead of just one).


# Consider maybe using the Collections module, http://docs.python.org/library/collections.html
# E.g. the namedTuple (static, immutable, hashable) or OrderedDict (volatile, mutable, unhashable) classes
# Note: namedTuple(typename, field_names) is a factory function, e.g. it creates a _Class_

# In perspective to compare oligos in designs: It should surely be possible to
# compare both oligos between two (or a new vs all existing) modules, and also
# compare oligos between two (or a new vs all existing) DESIGNS. (E.g. to quickly
# investigate which changes has been made between a new design and the previous design
# - and to determine that an equivalent design does not already exist).

"""
Old, mostly deprechated module containing various auxillary functions.
In hindsight, the functions should have been grouped at the module level,
and not hidden as class functions or object methods.

"""



import csv, re
from StringCompareLimit import StringCompareLimit

class OmToolbox:
    def printSetDiff(self, org, new):
        myset = org & new
        print 'Common to both sets: ' + str(len(myset)) + ' elements'
        for elem in myset: # Same as org.intersection(new)
            print elem
        print
        myset = org - new # Same as org.difference(new)
        print 'Removed (org set minus new set): ' + str(len(myset)) + ' elements'
        for elem in myset:
            print elem
        print
        myset = new - org
        print 'Added (new set minus org set): ' + str(len(myset)) + ' elements'
        for elem in myset: # Same as new.difference(old)
            print elem

    def compareOligoSets(self, org, new):
        print "1) Extract oligos and just compare the two sets:"
        print "2) Compare full set (adding annotations, etc)"
        wtd = input_raw('What to do')


    def compareSetAgainstMany(self, existing_sets, new):

        itm_changed_score = list()
        for i,org in enumerate(existing_sets):
            pass

    """Investigate the difference a bit more elaborate, e.g. compare the
    "changed" (difference_symmetric) oligos and see how exactly the new set has changed"""
    def compareSetDetailedDiff(self, org, new):
        pass


    def printSetDiffWithStringCompare(self, org, new, orgseqdict=None, newseqdict=None):

        if orgseqdict is None and hasattr(org, 'seqdict'):
            orgseqdict = org.seqdict

        if newseqdict is None and hasattr(new, 'seqdict'):
            newseqdict = new.seqdict

        limit = 0.8
        comparator = StringCompareLimit(limit=limit)
        myset = org & new

        print 'Common to both sets: ' + str(len(myset)) + ' elements'
        for elem in myset: # Same as org.intersection(new)
            eleminfo = ''
            if not orgseqdict is None:
                if elem in orgseqdict: eleminfo = " " + str(newseqdict[elem])
            else: eleminfo = " (no info-)"
            print elem + eleminfo
        print
        myset = org - new # Same as org.difference(new)
        print "Removed: (oligos which were present in %s set but not in %s set) %s elements'" % ("old", "new", str(len(myset)))
        print "limit = " + str(limit)
        similarCount = 0
        for elem in myset:
            eleminfo = ''
            if not orgseqdict is None:
                if elem in orgseqdict: eleminfo = " " + str(orgseqdict[elem])
            else: eleminfo = " (no info-)"
            print "Removed from org set: " + elem + eleminfo
            similarOligos = list()
            for oligo in new:
                similarity = comparator.recalculate(elem, oligo)
                if not newseqdict is None:
                    if oligo in newseqdict: oligoinfo = " " + str(newseqdict[oligo])
                else: oligoinfo = " (no info)"
                if similarity > limit:
                    similarOligos.append(oligo)
                    #self.printSimilar(oligo, len("Removed from org set: "), newseqdict[oligo])
                    print "\- - Similar to:           "[0:len("Removed from org set: ")] + oligo + oligoinfo
            if len(similarOligos) > 0: similarCount += 1
            #print "".join(['-Similar to '] + similarOligos)
        print "Summary: "+str(len(myset))+" oligos removed, "+str(similarCount)+" of these are similar to oligos in the new set."


        myset = new - org # Same as new.difference(old)
        print ""
        print 'Added (new set minus org set): ' + str(len(myset)) + ' elements'
        print "limit = " + str(limit)
        similarCount = 0
        for elem in myset:
            eleminfo = ''
            if not newseqdict is None:
                if elem in newseqdict: eleminfo = " " + str(newseqdict[elem])
            else: eleminfo = " (no info-)"
            print "Added to new set: " + elem + eleminfo
            similarOligos = list()
            for oligo in org:
                similarity = comparator.recalculate(elem, oligo)
                if similarity > limit:
                    similarOligos.append(oligo)
                    if not orgseqdict is None:
                        if oligo in orgseqdict: oligoinfo = " " + str(orgseqdict[oligo])
                    else: oligoinfo = " (no info)"
                    print "\- - Similar to:           "[0:len("Added to new set: ")] + oligo + oligoinfo
            if len(similarOligos) > 0: similarCount += 1
            #print "".join(['-Similar to '] + similarOligos)
        print "Summary: "+str(len(myset))+" oligos removed, "+str(similarCount)+" of these are similar to oligos in the old set."

    def printSimilar(self, oligo, prefixlength, seqdict):
        if seqdict==None:
            postfix = 'hello...'
        else:
            postfix = "--INFO: " + str(seqdict)
        prefix = '\-- Similar to:' + ' '*20
        prefix = prefix[0:prefixlength-2]
        return " ".join([prefix, oligo, postfix])

    def PrintOrderListFromCadnanoSet(self, cadnanofile, groupalias):
        #omsetreader = OmSetReader(mismapfilepath='default')

	# Note, I introduced a bug when I switched from a dict[i] to a list (which starts at 0)
        map = ['T'*i for i in range(0,20)]


        if isinstance(cadnanofile, str):
            try:
                fp = open(cadnanofile, "rU")
                #print "Opened " + cadnanofile
            except csv.Error:
                print "Could not open <str> cadnanofile: " + cadnanofile
        else: fp = cadnanofile

        reader = csv.reader(fp, delimiter='\t')

        lineisheader = True

        header = list()
        data = list()

        for line in reader:
            if lineisheader:
                lineisheader=False
                header = line
                print "\t".join(["Alias", "\t".join(line[2:3])])
            elif len(line) > 2:
                line[2] = self.mapseq(line[2], '\?', map)
                uniqueflag = True
                for previousline in data:
                    if line[2] == previousline[2]:
                        uniqueflag = False
                        if line == previousline: print "The following sequence was already added:"
                        else:
                            print "WARNING: The following sequence was already added, but the two lines were not completely identical:"
                            print "previous line: " + previousline
                        print "line: " + line
                if uniqueflag:
                    data.append(line)
                    print "".join([groupalias, ":", line[0], "-", "\t".join(line[1:3])])
            else:
                #print "Short (possibly empty) line: " + "\t".join(line)
                pass

    def mapseq(self, seq, mapchar=None, map=None):
        match = re.search(mapchar+'+', seq)
        if match is None:
            return seq
        else:
            return "".join([seq[0:match.start()], map[len(match.group())], self.mapseq(seq[match.end():], mapchar, map)])


if __name__ == "__main__":
    pass

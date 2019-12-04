# -*- coding: utf-8 -*-
"""
Created on Fri Dec 17 11:40:24 2010

@author: Rasmus Scholer Sorensen
"""

import csv, re

class OmDesign:
    def __init__(self, oligoset=None):
        pass



class OmSetReader:
    def __init__(self, filepath=None, mismapfilepath=None, delimiter=None):
        """The 'mismap' is used for mapping sequences with unknown characters such as 'X' or '?' to a proper sequence."""
        self.filepath = filepath

        if mismapfilepath is None:
            self.mismapper = None
        if mismapfilepath == 'default':
            self.mismapper = self.getDefaultMismapper()
        if mismapfilepath == 'allT':
            self.mismapper = self.getAllTMismapper()

        if isinstance(filepath, str):
            if delimiter is None:
                with open(filepath, "rU") as fp:
                    try:
                        delimiter = csv.Sniffer().sniff(fp.read(1024)).delimiter
                    except csv.Error:
                        print("csv.Sniffer could not determine file delimiter. Using ','.")
                        delimiter = ','


            # the doc example is with csv.reader; csv.DictReader doesn't work!
            # This is because csv.DictReader(<file>, csv.dialect).fieldnames returns a csv.dialect object (??)
            # and not a list of fieldnames (or just a string or whatever...)
            csvreader = csv.DictReader(open(filepath), delimiter=delimiter)

            #self.csvreader = csvreader # Should be commented out
            #self.oligoset = self.getSetFromDictList(csvreader, self.mismapper)
            self.oligoset, self.seqdict = self.getSetAndSeqDictFromDictList(csvreader, self.mismapper)


    def getSetFromDictList(self, dictlist, mismapper=None):
        myset = set()
        mapchar = '[X\?]'
        for row in dictlist:
            header_seq = self.getSeqHeader(row)
            if header_seq == 0:
                print("header_seq == 0")
                pass
            elif mismapper is None:
                #print row[header_seq] + " --> mismapper is none"
                myset.add(row[header_seq])
            else:
                new = self.mapseq(row[header_seq], mapchar, mismapper)
                #print row[header_seq] + "-->"
                #print new
                myset.add(new)

        return myset

    def getSetAndSeqDictFromDictList(self, dictlist, mismapper=None):
        myset = set()
        mydict = dict()
        mapchar = '[X\?]' # Should only be hardcoded during dev-test phase.
        for row in dictlist:
            header_seq = self.getSeqHeader(row)
            if header_seq == 0:
                print("header_seq == 0")
                pass
            elif mismapper is None:
                #print row[header_seq] + " --> mismapper is none"
                myset.add(row[header_seq])
                mydict[row[header_seq]] = row
            else:
                newseq = self.mapseq(row[header_seq], mapchar, mismapper)
                #print row[header_seq] + "-->"
                #print new
                myset.add(newseq)
                mydict[newseq] = row

        return (myset, mydict)

    def mapseq(self, seq, mapchar=None, map=None):
        if mapchar == '?': mapchar = '\?'  # Just in case you are really sloppy...
        if mapchar == None: mapchar = '\?'
        if map == None: map = self.mismapper
        #print "Seq: " + seq
        match = re.search(mapchar+'+', seq)
        if match is None:
            return seq
        else:
            #print "Before: " + seq[0:match.start()]
            #print "Match: " + match.group()
            #print "After: " + seq[match.end():]
            #print match.group()
            lst = [seq[0:match.start()], map[len(match.group())], self.mapseq(seq[match.end():], mapchar, map)]
            return "".join(lst)

    def getSeqHeader(self, rowdict):
        bestHeaders = ['sequence_mod', 'sequence']
        for key in list(rowdict.keys()):
            if key.lower() in bestHeaders:
                return key
        for key in list(rowdict.keys()):
            if key.lower().find('sequence')>=0:
                return key
        return 0


    def getDefaultMismapper(self):
        # A mismapper is a mapper that maps a number to a sequence.
        mapper = dict()

        for i in range(1, 20):
            mapper[i] = 'T'*i

        return mapper

    def getAllTMismapper(self):
        ## A dict that simply maps '?'*i -> 'T'*i for all lengths up to 300. Should be sufficient.
        return dict([(i,'T'*i) for i in range(1,300)])

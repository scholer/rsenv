# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 09:25:39 2013

Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com

@author: scholer
"""


import numpy as np # use as np.arange(...)
from matplotlib import pyplot # use as pyplot.scatter(...)
import operator
from collections import OrderedDict
import random


class SampleNameManager():
    def __init__(self):
        self.Prefs = dict()
        self.SamplePosMap = None
        self.SampleNames = None


        
    # get sample names:
    def readSamplenames(self, samplenamesfile):
        with open(samplenamesfile) as f:
            samplenames = [line.strip() for line in f if line.strip()[0] != "#"]
        self.SampleNames = samplenames
        return samplenames


    def makeSampleNamePosMap(self, sampleposfile):
        with open(sampleposfile) as f:
            #metadata = f.readline()
            header = f.readline().strip().split('\t')
            # edit: instead of having a list of lists, I change so I have a list of dicts.
            sampleposdata = [dict(zip(header, line.strip().split('\t'))) for line in f if line.strip()[0] != "#"]
        sampleposmap = dict([(entry["General:Pos"], entry["General:Sample Name"]) for entry in sampleposdata])
        self.SamplePosMap = sampleposmap
        return sampleposmap #, sampleposdata





    def indexToRowColTup(self, index, ncols=12, nrowmax=8, reverse=False):
        """ Convert a linear index integer to row-column tuple, e.g. 8 -> (1,2)
            Is used to convert src-plate positions.
            # ROW in German is Zeile, Column is Saule
            # epMotion index starts at 1, i.e. A1 is Z=1, S=1; A2 <=> Z=1, S=2, etc.
        """
        # destindex is defined by "for destindex, moduletopipet in enumerate(modulestopipet):" 
        # index = 0 should return (1,1), index = 1 return (1,2), index 11 return (1,12), index 12 return (2,1).
        index = int(index) # Doing cast is ok, but adding or subtracting anything just causes confusion.
        if reverse:
            index = ncols*nrowmax-1 - index
    #    print "indexToRowColTup(): index: {} --vs-- ncols: {} ; nrowmax: {}".format(index, ncols, nrowmax)
        col = (index % ncols) +1 # Watch out for modulus, returns from 0 to N-1.
        row = (index/ncols) +1 # NOTE: Python 2 specific. Use floor (math module) for python3
        if row > nrowmax:
            print "indexToRowColTup() WARNING > index {0} with ncols={1}, nrowmax={2} will return a row of {3}, exceeding the limit!".format(index, ncols, nrowmax, row)  
        return (row,col)
    
    
    def indexToRowColTupColWise(index, ncols=12, nrowmax=8, reverse=False):
        """
        Like indexToRowCol, but in col wise fashion. 
        If reverse=True, then return the pos/row-col-tup as it would be if the plate was rotated 180 degree.
          -- I.e., 0->H12, 1=H11, 7=H01, 8=G12, ...
        Alternatively, you could make an index-to-index, but that seems hard...
        """
        index = int(index) # Make sure we have integer.
        if reverse:
            index = ncols*nrowmax-1 - index   # -1 because we use 0-based index, not 1.
        col = (index/nrowmax) +1 # Watch out for modulus, returns from 0 to N-1.
        row = (index % nrowmax) +1 # NOTE: Python 2 specific. Use floor (math module) for python3
    #    print "indexToRowColTupColWise(): index: {} --vs-- ncols: {} ; nrowmax: {} --yields-- ({},{})".format(index, ncols, nrowmax,row,col)
        return (row,col)
    
    
    def indexToPos(index, ncols=12, nrowmax=8, colwise=False, reverse=False):
        indextotupfun = indexToRowColTupColWise if colwise else indexToRowColTup
        row,col = indextotupfun(index, ncols, nrowmax, reverse=reverse)
        pos = rowcolToPos(row,col)
        return pos
    
    def rowcolToPos(row,col,zeropad=False):
        fmtstr = "{0}{1:02}" if zeropad else "{0}{1}"
        pos = "{0}{1}".format(chr(ord('A')+row-1),col)     # edit: No zero-padding for light-cycler !    (used to be {0}{1:02})
        #print pos
        return pos
    
    
    
    
    
    def makeflatsamplelist(samplenamesfile, samplefilereplicatetuples):
        """
        Takes a tuple construct specifying files with sample names, 
        and a number specifying the number of replicates for each 
        samplename in that file, as:
        [(samplenames_triplicates, 3), (samplenames_duplets, 2), etc]
        Extends this to a "flat" list, as:
        ["samplenameA, 1", "samplenameA, 2", etc...]
        This list is written to the samplenamesfile file.
        """
    
        #nsamplerep = 3
    
        # new code:
        samplenames = list()
        with open(samplenamesfile, 'wb') as g:
            for filename, nsamplerep in samplefilereplicatetuples:
                with open(filename) as f:
                    for line in open(filename):
                        if line.strip()[0] == "#":
                            continue
                        for i in range(nsamplerep):
                            samplename = line.strip()+ ", {}".format(i+1) if nsamplerep > 1 else line.strip()
                            samplenames.append(samplename)
                            g.write(samplename+"\n")
    
        # old code:
        # First, make the flat (i.e. sample replicates)
    #    with open(samplenamesfilereplicates) as f1, open(samplenamesfileother) as f2, open(samplenamesfile, 'wb') as g:
    #        samplenames = list()
    #        for line in f1:
    #            for i in range(nsamplerep):
    #                if line.strip()[0] != "#":
    #                    samplename = line.strip()+ ", {}".format(i+1)
    #                    samplenames.append(samplename)
    #                    g.write(samplename+"\n")
    #        for line in f2:
    #            if line.strip()[0] != "#":
    #                samplenames.append(line.strip())
    #                g.write(line)
    
        return samplenames
    
    
    def makesamplelistextended(samplenamesflat, samplenamesextendedfile, nqpcrrep=2, colwise=False, qpcrrepcolwise=False, reverserack=False, plateformat=None):
        """
        Arguments:
         - samplenamesflat is a list of sample names, in a flat, linear order.
         - samplenamesextendedfile: output file, specifying a sample name for each position in the qPCR well plate.
         - colwise: samples are ordered colwise, i.e. first sample in A1, second in B1, etc. If false (i.e. rowwise), then second sample is next to sample 1 in row A.
         - qpcrrepcolwise: specifies whether qpcr replicates are below each other columnwise, else they are next to each other rowwise
         - reverserack: if you have turned the whole rack 180 degree at some point, set this to true and it will compensate.
         - plateformat: tuple(ncols, nrows) specifying the number of columns, rows and number of wells in the plate (=ncols*nrows)
         
        """
    
        if isinstance(samplenamesflat, basestring):
            with open(samplenamesflat) as f:
                samplenames = [line.strip() for line in f if line.strip()[0] != "#"]
            samplenamesflat = samplenames
    
        if plateformat is None:
            plateformat = (24, 16) # (ncols, nrows)
        ncols = plateformat[0]
        nrows = plateformat[1]
        index = 0
    
        with open(samplenamesextendedfile,'wb') as f:
            f.write("General:Pos\tGeneral:Sample Name\n")
            for si,samplename in enumerate(samplenames):
                for i in range(nqpcrrep):
                    if qpcrrepcolwise == colwise:
                        # This is the simple case, all samples in linear order:
                        pos = indexToPos(index, ncols=ncols,nrowmax=nrows,colwise=colwise,reverse=reverserack)
                    elif qpcrrepcolwise == False:
                        # Samples are colwise, but qpcr replicates are side by side, rowwise.
                        scol = si / nrows # attention: zero-based col. A01=0, A02=1, etc.
                        srow = si % nrows # attention: zero-based row. A=0, B=1, etc.
                        realrow = nrows-srow if reverserack else srow+1
                        realcol = ncols-(scol*nqpcrrep+i) if reverserack else scol*nqpcrrep+i+1 # 0(1)=1, 1(2)=3, 
                        pos = rowcolToPos(realrow, realcol)
                    else:
                        raise NotImplementedError("Not implemented yet, not needed yet...")
                    f.write("{0}\t{line}\n".format(pos, line=samplename))
                    index += 1


if __name__ == "__main__":

    testing = False
    if testing:
        indextestseq = [0,1,7,8,11,12,15,16, 383,383-1,383-8*2,383-8*2-1] #" remember, start is index=0, end is index=383
        for index in indextestseq:
            tup = indexToRowColTupColWise(index, ncols=2*12, nrowmax=8*2, reverse=True)
            pos = indexToPos(index, ncols=2*12, nrowmax=8*2, colwise=True, reverse=True)
            print "index {} -> tup {} -> pos {}".format(index, tup, pos)
        exit()
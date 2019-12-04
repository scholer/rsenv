#!/usr/bin/python

# Compare two oligo-design-sets:
# From csv-files, using columns from header seqence_mod
# TIP: os.getcwd() - current working directory...

#import OmToolbox, 
#import csv #, os

import os
from OmToolbox import OmToolbox
from OmSetReader import OmSetReader


#print "Start script..."
#cwd = os.getcwd()
#print "Working directory: %s" % cwd

#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.ZZandSScombined.set', 'default')
#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.SS.independent.set' , 'default')
#newdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.ZZ.RScolor.set', 'default')
#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.Rothemund_from-s1.csv' , 'default')


#newdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.SS.i-4T.set' , 'default')
#newdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.ZS.i-4T.set' , 'default')
#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.ZZ.i-4T.set' , 'default')

#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/Smallbox/NE_OrderList12-23-2010.csv' , 'default', ',')
#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/Smallbox/Smallbox-order-2.txt' , 'default', '\t')
#newdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/orderlists/smallboxorder.list' , 'default', '\t')
#orgdesign = OmSetReader('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/Smallbox/c10_RSandReza4_corrections8.set' , 'default')

orgdesign = OmSetReader('example_files/Box.Closed.jan09.csv', 'default')
newdesign = OmSetReader('example_files/Box.Closed.Jan09.set', 'default')




#print newdesign.oligoset
#print newdesign.seqdict['TTTTTTAAGCGTCTTTCCAGAGCCTTACCAAC']

#print orgdesign.seqdict['ACCTGCTCTGATAAATTGTGTCGATTTAATTCTGC']

#newset,newdict = getSetAndSeqDictFromDictList

#print newdesign.csvreader
#print newdesign.csvreader.dialect
#print newdesign.csvreader.next()
# print newdesign.oligoset



tbx = OmToolbox()


#tbx.PrintOrderListFromCadnanoSet('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/TallRectangle/TR.SS.i-4T.set', 'TR')
#tbx.PrintOrderListFromCadnanoSet('/home/scholer/Documents/Dropbox/Aktuel forskning/Modelling_Design/caDNAno/Smallbox/c10_RSandReza4_corrections8.set', 'SB')
#tbx.PrintOrderListFromCadnanoSet('Smallbox/c10_RSandReza4_corrections8.set', 'SB')


tbx.printSetDiffWithStringCompare(orgdesign.oligoset, newdesign.oligoset, orgdesign.seqdict, newdesign.seqdict)
#tbx.printSetDiff(orgdesign.oligoset, newdesign.oligoset)

#tbx.PrintOrderListFromCadnanoSet('example_files/Box.Closed.jan09_c208_syncing.set')

#print "done"

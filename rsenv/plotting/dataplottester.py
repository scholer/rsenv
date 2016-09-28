#!/usr/bin/python
# -*- coding: utf-8 -*-


import DataPlotter

file1 = "B1VandCy3ebbed1.dat"
file2 = "PVC.pvc"
#dreader = DataPlotter.DataReader(scheme='simplecsv')
#dreader.setDialectByExampleFile(file1)
#print "Delimiter: '" + dreader.Dialect.delimiter +"'"
#dso = dreader.readFile(file1)
##
##dreader = DataPlotter.RsDataReader(scheme='pvc')
##dso = dreader.readFile(file2)
##print len(dso.Data)
##print len(dso.Data[0])
##print len(dso.Data[1])
##print dso.Data[0][0:10]
##print dso.Data[1][0:10]
##print dso.Data[1][-10:-1]
##print dso.Data[0][-10:-1]
dplotter = DataPlotter.RsDataPlotter(scheme='pvc')
dplotter.Plottitle = 'My test'
filelist = ['PVC.pvc', 'PVC2.pvc']
dplotter.plotfiles(filelist)



print("\nTest script completed.")
#!/usr/bin/env python
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
Created on Fri Feb 8 2013

@author: scholer

Includes various python code that I use frequently for parsing nanodrop files (.ndj).
"""


""" Get data from nanodrop data file (.ndj) input as string or file-object.
    Data is returned as a list of lists, with stripped string elements.
    
    SEE ALSO:
     - ComponentAnalyser.py 
     - DataPlotter.py (old; for PVC and CSV files)
     - FluoromaxDataPlotter.py 
"""
def get_data(datafile):
    if isinstance(datafile, basestring):
        datafile = open(datafile)
    
    print "data = [[elem.strip() for elem in line.split('\t')] for line in datafile]"
    data = [[elem.strip() for elem in line.split('\t')] for line in datafile]
    return data

def get_metadata(data):
    #print 'meta["headers"] = data[4]'
    #print 'meta["xdomain"] = headers[17:]'
    headers = data[4]
    xdomain=headers[17:]
    return dict( headers=headers,
                 xdomain=xdomain)

def get_measurements(data):
    #print "measurements = data[5:]"
    measurements = data[5:]
    return measurements

def get_samplelist(data):
    measurements = data[5:]
    sampleids = [m[0] for m in measurements]
    return sampleids

def get_data_for_xvals(data, xvals, sample=0,doprint=False):
    #print "One-liner: for i in range(250,270): "
    #print "print str(i) + ': ' + [elem.strip() for elem in data_raw[6].split('\t')][ [elem.strip() for elem in headers.split('\t')].index('{:.1f}'.format(float(i))) ]"
    measurements = data[5:]
    headers = get_metadata(data)["headers"]
    if xvals is None:
        xvals = get_metadata(data)["xdomain"]
    if isinstance(sample,basestring):
        sample = [m[0] for m in measurements].index(sample)
    measurement = measurements[sample]
    yvals = [measurement[headers.index('{:.1f}'.format(float(xval)))] for xval in xvals]
    if doprint:
        for i,xval in enumerate(xvals):
            print "{xval}: {yval}".format(xval=xval, yval=yvals[i])

    return yvals

""" Testing """

if __name__ == "__main__":
    print "Starting test of module rsnanodrop.py ----"

    datafile="/home/scholer/Documents/Dropbox/_experiment_data/equipment_data_sync/Nanodrop/Nucleic Acid/Default/today.ndj"
    data = get_data(datafile)
    print get_metadata(data)
    #print get_measurements(data)
    print get_samplelist(data)
    get_data_for_xvals(data,range(250,280),sample='RS126h1',doprint=True)

    print "Finished test of module rsnanodrop.py ^^^^ "


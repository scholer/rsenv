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
Created on Fri Feb 8 2013

@author: scholer

Includes various python code that I use frequently for parsing nanodrop files (.ndj).
Note: This file contains anything related to parsing and handling of nanodrop files.
rsplot/rsnanodropplotter.py contains code for plotting (it uses this library for parsing!)

Note: This is not for parsing the NanoDrop workbook format, (.tbwk).

SEE ALSO:
 - ComponentAnalyser.py
 - DataPlotter.py (old; for PVC and CSV files)
 - FluoromaxDataPlotter.py

"""

from __future__ import print_function, absolute_import
import os
import glob
from builtins import input
from six import string_types


def get_data(datafile):
    """
    Get data from nanodrop data file (.ndj) input as string or file-object.
    Data is returned as a list of lists, with stripped string elements.
    ACTION: data = [[elem.strip() for elem in line.split('\t')] for line in datafile]
    Notice: The first five (5) lines in the ndj file is metadata..."""
    if isinstance(datafile, string_types):
        datafile = open(datafile)
    data = [[elem.strip() for elem in line.split('\t')] for line in datafile]
    return data

def get_metadata(data):
    #print 'meta["headers"] = data[4]'
    #print 'meta["xdomain"] = headers[17:]'
    headers = data[4]
    xdomain=headers[17:]
    lightpath = data[1][1]
    #print "Lightpath: {0}".format(lightpath)
    return dict( headers=headers,
                 xdomain=xdomain, lightpath=lightpath)

def get_measurements(data):
    #print "measurements = data[5:]"
    measurements = data[5:]
    return measurements


def get_samplelist(data):
    measurements = data[5:]
    sampleids = [m[0] for m in measurements]
    return sampleids


def get_sampleindex(sample, data):
    try:
        sample = int(sample)
    except ValueError:
        measurements = data[5:] # Do not include the first five lines.
        sample = [m[0] for m in measurements].index(sample)
    return sample


def get_data_for_xvals(data, xvals=None, sample=0,doprint=False,returnTuple=False):
    #print "One-liner: for i in range(250,270): "
    #print "print str(i) + ': ' + [elem.strip() for elem in data_raw[6].split('\t')][ [elem.strip() for elem in headers.split('\t')].index('{:.1f}'.format(float(i))) ]"
    measurements = data[5:]
    headers = get_metadata(data)["headers"]
    if xvals is None:
        xvals = get_metadata(data)["xdomain"]
    sample = get_sampleindex(sample, data)
    measurement = measurements[sample]  # Basically just the line in the ndj file; offset by 5.
    yvals = [float(measurement[headers.index('{:.1f}'.format(float(xval)))]) for xval in xvals]
    if doprint:
        for i, xval in enumerate(xvals):
            print("{xval}: {yval}".format(xval=xval, yval=yvals[i]))

    if returnTuple:
        return (yvals, xvals, sample)
    else:
        return yvals


def select_ndj_file(path=None):
    if path is None:
        path = os.getcwd()
    else:
        raise NotImplementedError("Specifying a path in select_ndj_file() is not implemented.")
    ndjfiles = sorted(glob.glob("*.ndj"))
    if len(ndjfiles) < 1:
        raise ValueError("No .ndj files found in directory '%s'" % path)
    print("Nanodrop files in directory:")
    print("\n".join(["[{0}] : {1}".format(i, ndjfile) for i, ndjfile in enumerate(ndjfiles)]))
    fileindex = input(("Which file do you want to plot data from? "
                       "(Hit enter to select the last file in list; use ctrl+c to cancel.)  "))
    if not fileindex:
        return ndjfiles[-1]
    try:
        fileindex = int(fileindex)
        try:
            datafile = ndjfiles[fileindex]
        except IndexError:
            print("IndexError: Perhaps you entered a wrong number?")
            datafile = select_ndj_file()
    except ValueError:
        # The user probably entered a filename...
        if fileindex in ndjfiles:
            pass
        else:
            print("Input not recognized...")
            datafile = select_ndj_file()

    return datafile


def produce_samplelist_for_files(printformat=None, filelist=None):
    """
    This is intended to make it easy to grep for a certain sample in a directory.
    Of course, I could also just use regular grep, but that also prints data and metadata for every measurement.
    printformat may include {samplename}, {sampleindex} and {filename}
    """
    if filelist is None or len(filelist)<1:
        filelist = sorted(glob.glob("*.ndj"))
    if printformat is None:
        printformat = "{filename}:{sampleindex} {samplename}"
    for ndj in filelist:
        data = get_data(ndj)
        print("\n".join(
            printformat.format(samplename=name, sampleindex=index, filename=ndj)
            for index, name in enumerate(get_samplelist(data))))



""" Testing """
if __name__ == "__main__":
    print("Starting test of module rsnanodrop.py ----")

    testfile="/home/scholer/Documents/Dropbox/_experiment_data/equipment_data_sync/Nanodrop/Nucleic Acid/Default/today.ndj"
    data = get_data(testfile)
    print(get_metadata(data))
    #print get_measurements(data)
    print(get_samplelist(data))
    get_data_for_xvals(data, range(250, 280), sample='RS126h1', doprint=True)

    print("Finished test of module rsnanodrop.py ^^^^ ")

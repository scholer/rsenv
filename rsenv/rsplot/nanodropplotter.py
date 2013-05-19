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

from rsenv.rsnanodrop_utils import *
from rsenv.rsexceptions import *
import rsenv.rsnanodrop_utils as nd_utils
from rsenv.rsfs_util import *
import os
import glob
# Other imports used in this file (will only be imported when functions are called to minimize
# initiation time of this module:
# import pylab
# from matplotlib import pyplot, font_manager



def plot_measurement(datafile=None, selection=None, interval=None, showplot=True):
    import pylab
    from matplotlib import pyplot, font_manager

    if datafile is None:
        try:
            datafile = nd_utils.select_ndj_file()
        except RsEmptyDirectoryError as e:
            print "No nanodrop (*.ndj) files in directory {0}!".format(e.Directory)
            return None
        except KeyboardInterrupt:
            print "KeyboardInterrupt; plotting cancelled completely.\n"
            return
#    print "Nanodrop files in directory: {0}  (using last one)".format(len(ndjfiles))
    print "Using nanodrop datafile: {0}".format(datafile)
    data = get_data(datafile)
    metadata = get_metadata(data)
    samplenames = get_samplelist(data)
    def select_ndj_samples(datafile, samplenames):
        print "=== SAMPLES in file '{}': ===".format(datafile)
        print "\n".join(["[{0}] : {1}".format(i, samplename) for i,samplename in enumerate(samplenames)])
        return raw_input("Which sample(s) do you want to plot? (separate with comma; use ctrl+c to cancel.) ")
    while selection is None or selection == '':
        try:
            selection = select_ndj_samples(datafile, samplenames)
        except KeyboardInterrupt:
            print "KeyboardInterrupt; Plotting of this file cancelled.\n"
            plot_measurement()
            return
        print "Selection is: {0}".format(selection)
        if selection == '':
            "Nothing selected. Please try again."
    if isinstance(selection, basestring):
        selection = selection.split(',')
    xdata = [float(val) for val in metadata["xdomain"]]
    legend = list()
    ymin,ymax = 0,0.1
    colors = "bgrcmy"
    linestyles = ('-', '--', ':')
    colorstyles = [(colors[i % len(colors)], linestyles[i / len(colors) % len(linestyles)]) for i in range(len(selection))]
    for i,sample in enumerate([sample.strip() for sample in selection]):
        sampleindex = get_sampleindex(sample, data)
        ydata = get_data_for_xvals(data, interval, sample, doprint=False)
        ymin = min(ymin,min(ydata))
        ymax = max(ymax,max(ydata))
        #ydata.append(get_data_for_xvals(data, interval, sample, False))
        # Plot using pyplot:
        label = samplenames[sampleindex]
        pyplot.plot(xdata, ydata, label=label, color=colorstyles[i][0], linestyle=colorstyles[i][1])
        #print "Label: {0}".format(label)
        legend.append(label)

    legend = tuple(legend)
    #print "Legend: {0}".format(legend)
    pyplot.xlabel("Wavelength (nm)")
    pyplot.ylabel("Absorbance (AU/{0})".format(metadata["lightpath"]))
    pyplot.title(datafile)
    pyplot.xlim(min(xdata), max(xdata))
    pyplot.ylim(ymin,ymax)
    #pyplot.legend(legend, prop={'size':'smaller'}, loc=0)
    if legend:
        # If I add labels during plot, I dont need to pass the legend labels; 
        # http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.legend
        pyplot.legend(prop={'size':12}, loc=0)
        # For some reason, my pyplot.legend does not understand a "fontsize" keyword, 
        # (nor "size" for that matter) despite what the documentation says.
#        pyplot.legend(shadow=True, size='small')

    if showplot:
        pylab.show()

    plot_again=raw_input("Do another plot?\n  Press 'y' or enter to plot with same datafile;\n  press 'f' to select a new file;\n  press 'n' or any other key to exit.\n")
    if len(plot_again)==0 or plot_again[0].lower() == 'y':
        plot_measurement(datafile)
    elif plot_again[0].lower() == 'f':
        plot_measurement()
        return



def plot_postprocessing(self, legend=None, title=None, export=False, showplot=False):
    import pylab
    from matplotlib import pyplot, font_manager
    pyplot.xlabel = "Wavelength (nm)"
    pyplot.ylabel = "Absorbance (AU/mm)"
    if legend:
        pyplot.legend(legend, prop={'size':'smaller'}, loc=0)
    if title:
        pyplot.title(title)
    
    
    if legend is None:
        legend = self.Legend
    scheme = self.Scheme
    title = self.Plottitle
    
    if self.Xlim:
        pyplot.xlim(self.Xlim[0], self.Xlim[1])
    
    if self.Ylim:
        pyplot.ylim(self.Ylim[0], self.Ylim[1])

    # For some reason, I have to save (export) BEFORE I show the plot, 
    # otherwise the saved png file is all empty.
    if self.Export:
        if self.ExportBasename:
            exportname = self.ExportBasename
        else:
            exportname = self.getTimebasedFilename()
        print "Saving plot as: "+ exportname
        pyplot.savefig(exportname, dpi=300)
    if self.Showplot:
        pylab.show()




""" Testing """

if __name__ == "__main__":
    """
    Note: To invoke this from command line, use the driver in rsenv/bin/nanodrop_plotsamples.py
    """
    print "Starting test of module rsnanodrop.py ----"
    
    start_dir = None
    test_dir = "/home/scholer/Documents/Dropbox/_experiment_data/equipment_data_sync/Nanodrop/Nucleic Acid/Default/"
    if len(glob.glob("*.ndj")) < 1:
        # No nanodrop data in current folder; probably just testing.
        start_dir = os.getcwd()
        os.chdir(test_dir)
#    datafile="/home/scholer/Documents/Dropbox/_experiment_data/equipment_data_sync/Nanodrop/Nucleic Acid/Default/today.ndj"
#    data = get_data(datafile)
#    print get_metadata(data)
    #print get_measurements(data)
#    print get_samplelist(data)
#    get_data_for_xvals(data,range(250,280),sample='RS126h1',doprint=True)

    plot_measurement()
    if start_dir:
        os.chdir(start_dir)
    print "Finished test of module rsnanodrop.py ^^^^ "


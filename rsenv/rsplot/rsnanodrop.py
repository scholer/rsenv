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
"""
def get_data(datafile):
    """
    get_data() ACTION: data = [[elem.strip() for elem in line.split('\t')] for line in datafile]
    Notice: The first five (5) lines in the ndj file is metadata..."""
    if isinstance(datafile, basestring):
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
        for i,xval in enumerate(xvals):
            print "{xval}: {yval}".format(xval=xval, yval=yvals[i])

    if returnTuple:
        return (yvals, xvals, sample)
    else:
        return yvals


def plot_measurement(datafile=None, selection=None, interval=None, showplot=True):
    import glob
    import pylab
    from matplotlib import pyplot, font_manager

    if datafile is None:
        datafile = select_ndj_file()
#    print "Nanodrop files in directory: {0}  (using last one)".format(len(ndjfiles))
    print "Using nanodrop datafile: {0}".format(datafile)
    data = get_data(datafile)
    metadata = get_metadata(data)
    samplenames = get_samplelist(data)
    if selection is None:
        print "=== SAMPLES in file '{}': ===".format(datafile)
        print "\n".join(["[{0}] : {1}".format(i, samplename) for i,samplename in enumerate(samplenames)])
        selection = raw_input("Which sample do you want to plot?  ")
    print "Selection is: {0}".format(selection)
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
        plot_measurement(select_ndj_file())



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


def select_ndj_file():
    import glob
    ndjfiles = sorted(glob.glob("*.ndj"))
    print "Nanodrop files in directory:"
    print "\n".join(["[{0}] : {1}".format(i, ndjfile) for i,ndjfile in enumerate(ndjfiles)])
    fileindex = raw_input("Which file do you want to plot data from? (Hit enter to select the last file in list)  ")
    if not fileindex:
        return ndjfiles[-1]
    try:
        fileindex = int(fileindex)
        try:
            datafile = ndjfiles[fileindex]
        except IndexError:
            print "IndexError: Perhaps you entered a wrong number?"
            datafile = select_ndj_file()
    except ValueError:
        # The user probably entered a filename...
        if fileindex in ndjfiles:
            pass
        else:
            print "Input not recognized..."
            datafile = select_ndj_file()

    print "Using nanodrop datafile: {0}".format(datafile)
    return datafile


def produce_samplelist_for_files(printformat=None, filelist=None):
    """
    This is intended to make it easy to grep for a certain sample in a directory.
    Of course, I could also just use regular grep, but that also prints data and metadata for every measurement.
    printformat may include {samplename}, {sampleindex} and {filename}
    """
    if filelist is None or len(filelist)<1:
        import glob
        filelist = sorted(glob.glob("*.ndj"))
    if printformat is None:
        printformat = "{filename}:{sampleindex} {samplename}"
    for ndj in filelist:
        data = get_data(ndj)
        print "\n".join([printformat.format(samplename=name, sampleindex=index, filename=ndj) for index,name in enumerate(get_samplelist(data))])



""" Testing """

if __name__ == "__main__":
    print "Starting test of module rsnanodrop.py ----"

    datafile="/home/scholer/Documents/Dropbox/_experiment_data/equipment_data_sync/Nanodrop/Nucleic Acid/Default/today.ndj"
#    data = get_data(datafile)
#    print get_metadata(data)
    #print get_measurements(data)
#    print get_samplelist(data)
#    get_data_for_xvals(data,range(250,280),sample='RS126h1',doprint=True)

    plot_measurement()
    print "Finished test of module rsnanodrop.py ^^^^ "


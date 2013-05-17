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
Created on Tue Mar  8 16:01:40 2011

@author: scholer
"""


## MOST IMPORTS HAVE BEEN MOVED TO FUNCTIONS OR CLASS INIT METHODS 
## to decrease the time it takes to load this module initially.

import os
import sys

# Additional required modules: numpy, scipy, pylab, csv, datetime.


class RsDataPlotter(object):
    
    def __init__(self, files=None, scheme=None, individualbatchexportmode=False):
    
        ## IMPORTS:
        import numpy, scipy
        #from pylab import plotfile, show, gca
        import pylab
        from matplotlib import pyplot, font_manager
        import csv
        import datetime
        self.Filelistfile = None
        self.Files = files
        #csv.register_dialect('fluoromax', delimiter='\t', quoting=csv.QUOTE_NONE)
        self.Labels = list() # X and Y labels, corresponding to RsDatasetObject.Headers
        self.Legend = None
        self.LegendLoc = 0
        self.Export = False
        self.ExportBasename = None
        self.Showplot = True
        self.Plottitle = None
        self.PlotEachFileIndividually = False # This activates a kind of 'batch' mode.
        self.UsePlotfileFunction = False
        self.DataReader = RsDataReader(scheme)
        if individualbatchexportmode:
            self.PlotEachFileIndividually = True
            self.Showplot = False
            self.Export = True

    def setScheme(self, scheme):
        self.DataReader.Scheme = scheme

    def getScheme(self):
        return self.DataReader.Scheme

    def setDialect(self, dialect):
        self.DataReader.Dialect = dialect
        
    def getDialect(self):
        return self.DataReader.Dialect
    
    Dialect = property(getDialect, setDialect)
    Scheme = property(getScheme, setScheme)

    def setByExample(self, filepath):
        self.DataReader.setByExample(filepath)
        print "Scheme is now: " + self.Scheme
        print "Dialect is now: " + str(self.Dialect)


    def plotfilelist(self, filelistfile, **kwargs):
        """ This method was originally developed for use in FluoromaxDataPlotter.py
        """
        fh = open(filelistfile)
        rdr = csv.reader(fh, dialect='excel-tab')
        filenames = list()
        captions = list()
        costumlines = list()
        for line in rdr:
            filename = line[0]
            if filename[0] == '#': 
                # Allow to comment out a line
                continue
            filenames.append(filename)
            if len(line) > 2:
                # Format is <color-char><style>, e.g. 'r--'
                costumlines.append((line[2][0], line[2][1:]))
            else: costumlines.append(None)
            
            if len(line) > 1: 
                captions.append(line[1])
            else:
                # Use the filename as caption
                captions.append(os.path.basename(line[0]))
        print "\n- ".join(["Files: "] + filenames)
        print "\n- ".join(["Captions: "] + captions)
        
        self.setByExample(filenames[0])
        self.plotfiles(filenames, captions, costumlines=costumlines, **kwargs)
                       #samePlot=samePlot, showplot=show,
                       #export=export, exportBaseName=basename, loc=loc, fontsize=fontsize,
                       #)


    ## NOTE THE CAPITAL "F" -- this method is a bit specialized. 
    ## the other plotfiles method is a bit easier to read and more general-purpose 
    ## (It will use this plotFiles if self.UsePlotfileFunction is set to True.)
    def plotFiles(self, filepaths, legend=None, export=False, exporttype='png', 
                  exportBaseName=None,
                  samePlot=False, delimiter='\t', showplot=False,
                  loc=0, fontsize='small', costumlines=None,
                  scheme='plotfile'
                ):
        """ This method was originally developed for use in FluoromaxDataPlotter.py
            I decided to merge this with the 'pvc' plotter to get a multi-potent plotting script.
        """
        if exportBaseName is None:
            exportBaseName = "Plot_"+str(datetime.datetime.now().strftime("%Y%m%d-%H%M"))
        newfig = not samePlot
        colors = "bgrcmy"
        linestyles = ('-', '--', ':')
        lines = list()
        for i in range(len(filepaths)):
            lines.append((colors[i % len(colors)], linestyles[i / len(colors) % len(linestyles)]))
        
        print lines
        
        #pyplot.hold(samePlot)
        print "filepaths: " + str(filepaths)
        print "samePlot: " + str(samePlot)
        for i,path in enumerate(filepaths):
            linecolor = lines[i][0]
            linestyle = lines[i][1]
            print "Plotting file: " + str(path)
            print "linestyle: " + linestyle
            if legend:
                caption = legend[i]
            else:
                caption = path
            if costumlines:
                if costumlines[i]:
                    linestyle = costumlines[i][1]
                    linecolor = costumlines[i][0]
            print "linecolor is: " + linecolor
            print "linestyle is: " + linestyle
            pyplot.plotfile(path, cols=(0,1), names=("Wavelength (nm)", caption),
                     delimiter=delimiter, checkrows=0, newfig=newfig, subplots=False,
                     label=caption, 
                     color=linecolor, linestyle=linestyle)
            if not samePlot:
                if export:
                    print "exporting individual plot..."
                    pyplot.savefig(exportBaseName+path, dpi=300)
        print legend
        print fontsize
        font = font_manager.FontProperties(size=14)
        # loc: 0 is "best", 1 upper right, 2 upper left
        # http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.legend
        if legend:
            pyplot.legend(legend, prop={'size':fontsize}, loc=loc)
        pyplot.ylabel("CPS")
        if export:
            if samePlot and exportBaseName:
                pyplot.savefig(exportBaseName, dpi=300)
                print "exporting collective plot"
            else: 
                print "plotFiles(): samePlot or exportBaseName is false."
                print " - samePlot: " + str(samePlot)
                print " - exportBaseName: " + str(exportBaseName)
        else:
            print "plotFiles(): export is False."
        if showplot:
            # I should probably use "pylab" namespace for these...
            pylab.show()


    def plotfiles(self, filepaths, legend=None, **kwargs):
        if legend is None:
            legend = self.getLegendFromFilepaths(filepaths)
        if self.UsePlotfileFunction:
            self.plotFiles(filepaths, legend=legend, **kwargs)
            return

        datasets = self.getDatasetFromFiles(filepaths)
        for ds in datasets:
            self.plotDataset(ds)

        self.postprocessing(legend, datasets)

    def postprocessing(self, legend=None, datasets=None):
        if legend is None:
            legend = self.Legend
        scheme = self.Scheme
        title = self.Plottitle
        
        if self.Xlim:
            pyplot.xlim(self.Xlim[0], self.Xlim[1])
        
        if self.Ylim:
            pyplot.ylim(self.Ylim[0], self.Ylim[1])
    
        if scheme == 'pvc':
            self.Labels.append('Wavelength (nm)')
            self.Labels.append('Absorbance (AU/cm)')
        elif scheme == 'FluoroMax':
            self.Labels.append('Wavelength (nm)')
            self.Labels.append('CPS')

        if len(self.Labels) > 1:
            pyplot.xlabel(self.Labels[0])
            pyplot.ylabel(self.Labels[1])
        elif datasets:
            if len(getattr(datasets[0], 'Headers', list())) > 1:
                pyplot.xlabel(datasets[0].Headers[0])
                pyplot.ylabel(datasets[0].Headers[1])
        if legend:
            pyplot.legend(legend, prop={'size':'smaller'}, loc=self.LegendLoc)
        else:
            print "No legend?"
        if title:
            pyplot.title(title)
        
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



    def getLegendFromFilepaths(self, filepaths):
        legend = list()
        for fp in filepaths:
            legend.append(os.path.basename(fp))
        self.Legend = legend
        return legend

    def checkFilepaths(self, filepaths):
        ok = list()
        for fp in filepaths:
            if os.path.exists(fp):
                ok.append(fp)
            else:
                print "Warning, file does not exists and will be excluded: " + fp
        self.Filepaths = ok
        return ok

    def getDatasetFromFiles(self, filepaths, snif=True):
        reader = self.DataReader
        if snif:
            reader.setDialectByExampleFile(filepaths[0])
        datasets = list()
        
        for fp in filepaths:
            datasets.append(reader.readFile(fp))
        return datasets


    def plotDataset(self, dataset, axes=None, showplot=False):
        """ Plot a RsDatasetObject, using the axes given (else the default).
        """
##        print "len(dataset.Data[0]): " + str(len(dataset.Data[0]))
##        print "len(dataset.Data[1]): " + str(len(dataset.Data[1]))
        pyplot.plot(dataset.Data[0], dataset.Data[1])
        if showplot:
            pylab.show()


    def getTimebasedFilename(self):
        """ Get a filename with the current time in it.
        """
        return "Plot_"+str(datetime.datetime.now().strftime("%Y%m%d-%H%M"))
        

class RsDataReader(object):
    """Object to read various file formats and return x and y values.
    """
    
    def __init__(self, scheme=None, dialect=None, useHeaders=False, columns=(), headers=()):
        """ If useHeaders is true, DataReader will try to read headers from the file.__class__
        If columns is defined, DataReader will restrict the returned dataset to those columns.
        If headers is defined (a tuple with strings), DataReader will apply use those headers.
        Note: In most circumstances, scheme will be enough to specify dialect, columns and headers.
        Standard dialects: 'excel', 'excel-tab'
        """
        import csv
        self.UseHeaders = useHeaders
        self.Columns = columns
        self.Headers = headers
        self.Data = list()
        
        self.Readers = dict() # Dict where scheme is key and value is a reader function
        self.Readers['simplecsv'] = self.readSimpleCsv
        self.Readers['pvc'] = self.readPvc
        
        self.Scheme = scheme
        self.Dialect = dialect # A None-dialect is better than a default dialect.

    
    def setByExample(self, filepath):
        # Try to figure out scheme and dialect using an example file
        if filepath[-4:].lower() == '.pvc':
            self.Scheme = 'pvc'
        else:
            # If all else fails:
            self.Scheme = 'simplecsv'
            self.setDialectByExampleFile(filepath)
    
    def setDialectByExampleFile(self, filepath):
        """ Not yet tested.
        """
        
        sniffer = csv.Sniffer()
        fo = open(filepath, "rb")
        dialect = sniffer.sniff(fo.read(2048))
        fo.close()
        self.Dialect = dialect
    
    def readFile(self, filepath, dstitle=None):#, columns=None, headers=None):
        """ Read file using the scheme provided on init and return a plotdata object.
        """
        with open(filepath, "rb") as fo:
            dataset = self.Readers[self.Scheme](fo, self.Columns)
        if not dstitle:
            dstitle = os.path.basename(filepath)
        dataset.Title = dstitle
        dataset.Headers = self.Headers
        
        return dataset
    
    def readSimpleCsv(self, fo, columns=None):
        if columns:
            pass
        elif self.Columns:
            columns = self.Columns
        reader = csv.reader(fo, self.Dialect)
##        data = [[row[i] for i in columns] if columns else 
##                [row[i] for i in range(len(row))] for row in reader] 
##        data = [[row[i] for row in reader] for i in columns if columns else ??] 
        #data = list()
        first = True
        # You could also use zip(), but that makes it harder to use 
        for row in reader:
            if first:
                if not columns:
                    columns = range(len(row))
                #data = [list()]*len(columns) # Wait! This is bad!
                # The above will give us a list of lists, but all the lists are actually the same object.__class__
                # The each entry in the list of lists references the same object.
                # Instead, use:
                data = list()
                for i in range(len(columns)):
                    data.append(list())
                first = False
            for i,col in enumerate(columns):
                data[i].append(row[col])

        return RsDatasetObject(data)

    def readPvc(self, fo, columns=None):
        """ Reads a PVC file from the "BioRad Nanophotometer"
        """
        datalines = [line for line in fo if line[0:4] == '$PXY']
        #print datalines
##        if len(datalines) < 1:
##            for line in fo
        rawdata = datalines[0].split(' ')
        # The first four are not actually data.append
        # Also, the last pair will have '\r\n' bytes, so lets just ignore those...
        rawdata = rawdata[4:-2]
        if len(rawdata) % 2:
            # If rawdata is uneven, try to remove the last element...
            rawdata.pop()
        data = [list(), list()]
##        for i,v in enumerate(rawdata):
##            data[i % 2].append(float(v))
        data[0] = rawdata[0::2]
        data[1] = rawdata[1::2]
        # Alternatively, use: data[0] = rawdata[0:2:] and rawdata[1:2:]
        ds = RsDatasetObject(data)
        ds.Headers = ('Wavelength (nm)', 'Absorbance (AU/cm)')
        return ds

class RsDatasetObject(object):
    
    def __init__(self, data=list(), title='', headers=None):
        """
            Data property is a list of equilateral lists
            Headers is a list of headers where Headers[i] is the header for Data[i]
        """
        self.Headers = headers
        self.Data = data
        self.Title = title







if __name__ == "__main__":
    """ NOTE: You should make use of argparse instead of this random logic."""
    import argparse
    
    # Get run-time options as a dict
    #options = getRuntimeOptions()
    
    argparser = argparse.ArgumentParser(description="""
This program will read one or several datafiles and plot them.
Currently recognized data schemes includes standard csv/tsv files and pvc files (from BioRad Photometer)
""")
#Syntax: dataplotter [--<handle> [hoptions]] <files-to-plot>
#where handle is one of:
#listfile <file>: specify a file which contains the files to plot (instead of specifying them here on the commandline)
#batchexportmode: used if you want to make a lot of individual graphs real quick.
#export: export the plot to a file
#showplot: make sure the plot is shown (this is default).
#title <title>: Specify a title for the plot.
#scheme <scheme>: the scheme to use. If no scheme is specified, it will try to figure it out automagically.
#"""
    
    argparser.add_argument('--listfile', default=None, dest='Plotlistfile', help="""
Specify data files to plot using a list instead of providing them on the command line.
    The scheme is that every line contains the following info (separated by tab):\n\
      file-to-plot       graph-legend     graph-style\n\
 e.g. BoxSpin1Cy5.dat    Box-spin1        r--""")

    argparser.add_argument('Plotfiles', nargs='*', metavar='datafile', 
                           help="One or more files to plot.")
    argparser.add_argument('--batchexportmode', action='store_true', dest="Batchmode",
                           help="Specifying batchexportmode is convenient for making a lot of individual graphs real quick.")
    # The old routine was to set dp.PlotEachFileIndividually = True AND dp.Export = True.
    argparser.add_argument('--export', action='store_true', dest='Export',
                           help="Export each plot to a file.")
#    argparser.add_argument('--showplot', action='store_true', dest='dp.Export',
#                            help="Make sure the plot is displayed on screen.")
    argparser.add_argument('--scheme', dest='Scheme', help="Specify the data scheme to use. Supported dataschemes currently includes: 'simplecsv', 'pvc' and 'FluoroMax'. Dataschemes are not only used while reading data but also for e.g. annotating the plot's axes etc.")
    argparser.add_argument('--title', dest='Plottitle', help="Specify a title for the plot.")
    argparser.add_argument('--Xlim', nargs=2, type=float, default=None, help="Specify the limits (DOMAIN) of the x-axis.")
    argparser.add_argument('--Ylim', nargs=2, type=float, default=None, help="Specify the limits (RANGE/IMAGE/CO-DOMAIN) of the y-axis.")

    dp = RsDataPlotter()
    argparser.parse_args(namespace=dp)

    if dp.Plotlistfile:
        print "Plotting files from filelist-file: " + str(dp.Plotlistfile)
        dp.plotfilelist(dp.Plotlistfile)
    elif dp.Plotfiles:
        print "\n- ".join(["Plotting files:"] + dp.Plotfiles)
        if not dp.Scheme:
            dp.setByExample(dp.Plotfiles[0])
        dp.plotfiles(dp.Plotfiles)
    else:
        print "Error, no plotfiles or plotlistfile given."
        argparser.print_help()

    ## ---- OLD CODE:  ----  ##
#    plotlistfile = None
#    plotfiles = list()

#    listfile = False
#    catchScheme = False
#    catchTitle = False
##    
#    for arg in sys.argv[1:]:
#        print arg
#        if arg.lower() == '--listfile':
#            listfile = True
#            continue
#        elif arg.lower() == '--batchexportmode':
#            dp.Export = True
#            dp.PlotEachFileIndividually = True
#            continue
#        elif arg.lower() == '--export':
#            dp.Export = True
#            continue
#        elif arg.lower() == '--showplot':
#            dp.Export = True
#            continue
#        elif arg.lower() == '--scheme':
#            catchScheme = True
#            continue
#        elif arg.lower() == '--title':
#            catchTitle = True
#            continue
#        
#        
#        if catchScheme:
#            dp.Scheme = arg
#            catchScheme = False
#            continue
#        elif catchTitle:
#            dp.Plottitle = arg
#            catchTitle = False
#            continue
#        if listfile:
#            plotlistfile = arg
#        else:
#            plotfiles.append(arg)
#    
#    
#    if plotlistfile:
#        print "Plotting files from filelist-file: " + str(plotlistfile)
#        dp.plotfilelist(plotlistfile)
#    elif plotfiles:
#        print "\n- ".join(["Plotting files:"] + plotfiles)
#        if not dp.Scheme:
#            dp.setByExample(plotfiles[0])
#        dp.plotfiles(plotfiles)
#    else:
#        print """
#Syntax: dataplotter [--<handle> [hoptions]] <files-to-plot>
#where handle is one of:
#listfile <file>: specify a file which contains the files to plot (instead of specifying them here on the commandline)
#batchexportmode: used if you want to make a lot of individual graphs real quick.
#export: export the plot to a file
#showplot: make sure the plot is shown (this is default).
#title <title>: Specify a title for the plot.
#scheme <scheme>: the scheme to use. If no scheme is specified, it will try to figure it out automagically.
#Currently recognized schemes:
# - simplecsv
# - pvc: datafiles from BioRad Photometer
#"""
## TIPS:
##            # Use a high number for checkrows, otherwise if the first 10 are ints 
##            # and the later are float, then plotfile/mlab.csv2rec will not have a float converter ready.
##            # Set checkrows to 0 to check all rows.

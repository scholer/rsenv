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

#import csv
#import datetime
#import numpy, scipy
#from pylab import plotfile, show, gca
#from matplotlib import pyplot, font_manager


class DataPlotter(object):
    
    def __init__(self, files=None):
        # IMPORTS:
        import csv
        import datetime
        import numpy, scipy
        from pylab import plotfile, show, gca
        from matplotlib import pyplot, font_manager

        self.files = files
        csv.register_dialect('fluoromax', delimiter='\t', quoting=csv.QUOTE_NONE)

    def plotfilelist(self, filelistfile, **kwargs):
#                     samePlot=True, export=None, show=False,
#                     loc=None, fontsize=None,
#                     basename="Plot_"+str(datetime.datetime.now().strftime("%Y%m%d-%H%M"))):
        #if export is None:
            # We want to allow the caller to add a export=None to let this function specify the default behaviour.
            # Actually, if the caller does this, just forward the export value with **kwargs.
        #    export = False
        #print "export is: " + str(export)
        fh = open(filelistfile)
        rdr = csv.reader(fh, dialect='fluoromax')
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
                captions.append(line[0])
        print "\n- ".join(["Files: "] + filenames)
        print "\n- ".join(["Captions: "] + captions)
        
        print loc
        self.plotFiles(filenames, captions, costumlines=costumlines, **kwargs)
                       #samePlot=samePlot, showplot=show,
                       #export=export, exportBaseName=basename, loc=loc, fontsize=fontsize,
                       #)
    

    def plotFiles(self, filepaths, legend=None, export=False, exporttype='png', 
                  exportBaseName=None,
                  samePlot=False, delimiter='\t', showplot=False,
                  loc=0, fontsize='small', costumlines=None):
        if exportBaseName is None:
            exportBaseName = "Plot_"+str(datetime.datetime.now().strftime("%Y%m%d-%H%M"))
        newfig = not samePlot
        colors = "bgrcmy"
        linestyles = ('-', '--', ':')
        lines = list()
        for i in range(len(filepaths)):
            lines.append((colors[i % len(colors)], linestyles[i / len(colors) % len(linestyles)]))
        
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
            plotfile(path, cols=(0,1), names=("Wavelength (nm)", caption),
                     delimiter=delimiter, checkrows=0, newfig=newfig, subplots=False,
                     label=caption, 
                     #ls='r--')
                     color=linecolor, linestyle=linestyle)
                     #)
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
            show()
        




if __name__ == "__main__":
    import sys
    plotlist = False
    plotlistfile = None
    plotfiles = list()
    sameplot = True
    export = None
    loc = None
    fontsize = None
    showplot = None # Be careful not to override show() callable
    delimiter = '\t'
    for arg in sys.argv[1:]:
        print arg
        if arg.lower() == '--listfile':
            plotlist = True
            sameplot = True
            continue
        elif arg.lower() == '--same-plot':
            sameplot = True
            continue
        elif arg.lower() == '--not-same-plot':
            sameplot = False
            continue
        elif arg.lower() == '--export':
            export = True
            print "export set to True."
            continue
        elif arg.lower() == '--showplot':
            showplot = True
            continue
        elif arg.lower() == '--legend-left':
            loc = 2
        elif arg.lower() == '--comma':
            delimiter = ','
            continue
        elif arg.lower() == '--smaller-font':
            fontsize = 'x-small'
            continue
        if plotlist:
            plotlistfile = arg
        else:
            plotfiles.append(arg)
    
    # Make it "sane", set default behaviour
    if export is None and showplot is None:
        showplot = True
        
    dp = DataPlotter()
    if plotlistfile:
        print "Plotting files from filelist-file: " + str(plotlistfile)
        dp.plotfilelist(plotlistfile, samePlot=sameplot, export=export, showplot=showplot, loc=loc, fontsize=fontsize)
    elif plotfiles:
        print "\n- ".join(["Plotting files:"] + plotfiles)
        dp.plotFiles(plotfiles, samePlot=sameplot, export=export, showplot=showplot, loc=loc, fontsize=fontsize)
    else:
        print "Uhm, no arguments. Really?"

## TIPS:
##            # Use a high number for checkrows, otherwise if the first 10 are ints 
##            # and the later are float, then plotfile/mlab.csv2rec will not have a float converter ready.
##            # Set checkrows to 0 to check all rows.

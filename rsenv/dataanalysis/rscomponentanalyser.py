#!/usr/bin/python
# -*- coding: utf-8 -*-
##    Copyright 2012 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

@author: scholer
"""

## MOST IMPORTS HAVE BEEN MOVED TO FUNCTIONS OR CLASS INIT METHODS 
## to decrease the time it takes to load this module initially.

import os
#import csv, datetime
#import numpy as np, scipy as sp
import matplotlib as mpl
# from matplotlib import pyplot as plt, font_manager # Easier shortcuts than mpl.pyplot
#import pylab # Pylab provides a matlab-like stateful model, e.g. "show", etc.
## Optionally: #from pylab import plotfile, show, gca
#import yaml        # Is loaded in YamlLoader:__init__()



def is_numeric(value):
    try:
        float(value)
        return True
    except:
        return False

def getDefaultParams():
    params = {}
    params['Xdataline'] = 5 # If 5, file reading effectively just skips the first four lines.
    params['PcDataLines'] = [10]#,19] # 7 is HEPES-KCl, 10 is STV 10 uM, 19 is ddUTP-DBCO. 
    #Note: Having 7 there gives a lot of noise. It might be nice to maximize a likelihood function rather than simple least-square. However, can be solved by adjusting the xrange used for analysis.
    params['AnalyteDataLines'] = [16]#,10] # 16 is RS100d-ret, 10 is just for phun.
    params['AnalysisRange']=(240, 320)
    params['PlotRange']=(None, None) # None means 
    params['Parameters Help'] = """
Xdataline : Define the line in the NDJ file that includes the X-data (and other headers/fields).
PcDataLines/AnalyteDataLines : List of lines defining lines in the NDJ file with Principal Components / Analytes, respectively.
AnalysisRange, PlotRange (xmin, xmax): What range to plot. Use None for no limit (full range)"""
    return params


class YamlLoader:

    def __init__(self):
        import yaml

    def loadParams(self, filepath):
        # You should refer to the oligomanager/staplemixer ConfigGenerator.py script in Dropbox/Dev/Projects/OligoManager2/oligomanager/staplemixer
        # One thing I found was that JSON does have the oppertunity to print line breaks in strings when dumping.
        # It might be able to do a little formatting, but I honestly prefer to practice using YAML for configs.
        # Thus: YAML for configs (human readable/editable), JSON for serial data, and xml for structured documents.
        # PyYAML ref: http://pyyaml.org/wiki/PyYAMLDocumentation
        with open(filepath, 'rb') as cfg:
            return yaml.safe_load(cfg) # Simple stuff should be loaded with safe_load...

    def saveParams(self, filepath, params):
        print("WARNING: Saving parameters does not preserve key order of the config/param file. /Rasmus")
        with open(filepath, 'wb') as cfg:
            yaml.dump(params, cfg, width=200)



class ComponentAnalyser:

    def __init__(self, debug=None, params=None, paramFile=None):
        """ paramFile will load first, then self.Parameters will be updated with params (dict).
        """
        # IMPORTS:
        import csv
        import datetime
        import numpy as np, scipy as sp
        import matplotlib as mpl
        from matplotlib import pyplot as plt, font_manager # Easier shortcuts than mpl.pyplot
        import pylab # Pylab provides a matlab-like stateful model, e.g. "show", etc.
        # Optionally: #from pylab import plotfile, show, gca


        if debug: self.Debug = debug
        else: self.Debug = 0
        # DebugSilentLevel is my own override switch. Set to 0 to let script behave silent except for errors.
        # The higher the value, the less the program will talk. Use -1 to be a little verbose.
        self.DebugSilentLevel = -1
        self.FileData = None
        self.Xrange = None
        self.Data = [] # list of dicts with items include description and ydata.
        # ca.Data includes all loaded data. It is a list of dicts, one dict per line, with fields 'Ydata','PcType' (Analyte or pc) plus all metadata fields of the Xdataline (E.g. 'Sample ID').
        # However, Data is mostly for reference. It is easier to use self.Xdata, self.Ydata <list of lists>, 
        #self.Ydataarrays = []# list of arrays, shortcut to self.Data[].Ydata - nope, use the Analyte or Pc attributes instead.
        #self.Datalabels = []# Corresponds to Self.Data[].Label
        self.Xdata = None
        # In my bachelorproject code I called it "bases" and "targets" rather than "PC" and "Analytes"...
        self.PcYdata = [] # Principal component spectro data
        self.PcLabels = []
        self.AnalyteLabels = []
        self.AnalyteYdata = []
        self.ConfigLoader = YamlLoader()
        self.Parameters = dict() # Optionally use getDefaultParams()
        if paramFile is not None:
            try:
                self.Parameters.update(self.ConfigLoader.loadParams(paramFile))
                if self.Debug > self.DebugSilentLevel: 
                    print("ComponentAnalyser() > Using parameters file: {}".format(paramFile))
            except IOError:
                print("ERROR : ComponentAnalyser() > Unable to locate parameter file: {}".format(paramFile))
        if params is not None:
            self.Parameters.update(params)
        self.PcResults = [] # Order corresponds to AnalyteYData, each entry is a tuple consisting of coefficients for each principal component.
        self.PcResult = dict() # A single dict to return result from np.linalg.lstsq. Coeff is under key 'PcCoeffs'.
        

    def findNdjFile(self, path="."):
        ndjfiles = [f for f in os.listdir(path) if f[-4:].lower()=='.ndj']
        if ndjfiles: return ndjfiles[0]
        else: return None

    def loadParams(self, filepath):
        params = self.ConfigLoader(filepath)
        self.Parameters.update(params)
        return params

    def saveParams(self, filepath):
        self.ConfigLoader(filepath, self.Parameters)


    """ READDATA method - Seems to work """
    def readData(self,path='.'):
        if os.path.isdir(path):
            ndjfilepath = self.findNdjFile(path)
        elif os.path.isfile(path):
            ndjfilepath = path
        else:
            print(" ".join(["Path '", path, "' does not refer to a valid file or directory!"]))
            return False
        if self.Debug > self.DebugSilentLevel:
            print("ComponentAnalyser.readData() > Using file: " + ndjfilepath)
        with open(ndjfilepath, 'rb') as ndj:
            # numpy readers include loadtxt and genfromtxt 
            #self.FileData = np.genfromtxt(ndj, delimiter='\t', skip_header=5, dtype=None)
            lineno=0
            xvaluesindex=[None, None]
            metadatamask = None
            xydatamask = None
            
            ## BY THE WAY: Consider casting to decimal type instead of float.http://docs.python.org/2/library/decimal.html
            
            for line in ndj:
                lineno+=1
                linedata = line.split('\t') # I know this is not required for the first lines, but it makes the program more readable.
                if lineno < self.Parameters['Xdataline']:
                    # Skip all lines above Xdataline
                    continue
                elif lineno == self.Parameters['Xdataline']:
                    # Use the Xdataline to retrieve xdata points and metadata fields.
                    #xdata = np.array() # Currently, I'm not using numpy arrays. Might change.
                    self.Xdata = list()
                    metadatamask = [] # False for numeric, value for string or other which indicates metadata fields.
                    for value in linedata:
                        try: 
                            self.Xdata.append(float(value)) # Should be float?
                            metadatamask.append(False) # A mask value of False means the datapoint is valid, i.e. entry is numeric.
                        except ValueError:
                            metadatamask.append(value) # Value is a metadata key (i.e. not an x-value...)
                    # Uh, this is actually opposite the standard. A True mask entry means "to mask", i.e. the entry is invalid.
                    # But here a mask entry of True is used to indicate proper/valid x data.
                    xydatamask = [(x == False) for x in metadatamask] # I prefer this over xydatamask = map(lambda x: (x == False), metadatamask) 
                    self.xydatamask = xydatamask # Keep for reference.
                else:
                    # Rest should be YDATA ENTRIES
                    #self.Datalabels.append(linedata[0]) # Should equal self.Data[i]["Sample ID"] # 
                    datadict = dict([(metadatamask[index], value.strip()) for index, value in enumerate(linedata) if metadatamask[index]]) # wow, if this works in the first try...
                    # for ydata: I could also just use if is_numeric(val), but I would like to have an exception thrown if val is not a float.
                    ydata = [float(val) for index, val in enumerate(linedata) if xydatamask[index]] 
                    datadict['Ydata'] = ydata # Xdata is the same for all...
                    if lineno in self.Parameters['PcDataLines']:
                        self.PcYdata.append(ydata)
                        self.PcLabels.append(linedata[0].strip())
                        datadict['PcType']='PC'
                    if lineno in self.Parameters['AnalyteDataLines']: # NOTE: Change back to elif not if.
                        self.AnalyteYdata.append(ydata)
                        self.AnalyteLabels.append(linedata[0].strip()) # Sample id is in the first column
                        datadict['PcType']='Analyte'
                    self.Data.append(datadict) # Save datadict later use...
        if self.Debug-self.DebugSilentLevel > 1:
            print("".join(['File: "', ndjfilepath, '" has been loaded.']))
            #print self.Xdata
            print("readData(): self.PcLabels : " + str(self.PcLabels))
            #print self.PcYdata
            print("readData(): self.AnalyteLabels : " + str(self.AnalyteLabels))
            #print self.AnalyteYdata
            print("readData(): self.Data[0].keys() : " + str(list(self.Data[0].keys())))


    def doPcAnalysis(self, xrng=None):
        """ xrng tuple (xmin, xmax) is the wavelength range to use. 
        Use None for no xmin/xmax. Default will use the complete spectrum. """
        """ This is broadly based on makeFitAndPlot from my bachelor's project..."""
        
        #Note: xrng is nolonger default to (None,None), but None, which then uses xrng in self.Parameters['AnalysisRange']
        if xrng is None:
            if 'AnalysisRange' in self.Parameters:
                xrng = self.Parameters['AnalysisRange']
            else:
                xrng = (None, None)
        if self.Debug-self.DebugSilentLevel > 0:
            print("ComponentAnalyser.doPcAnalysis() > x-range used for analysis: " + str(xrng))
        # Use xrng to provide indices.
        rngidx = [None, None] # Tuple does not support item assignment; is "static"
        for xrngindex, xrngval in enumerate(xrng):
            if xrngval is None:
                rngidx[xrngindex] = 0 if (xrngindex == 0) else len(self.Xdata)-1
            else: 
                index, xvalclosest = min(enumerate(self.Xdata), key = lambda iv: abs(iv[1]-xrngval)) # Take the absolute value.
                rngidx[xrngindex] = index
                if self.Debug > 0: print("index, xvalclosest : " + str((index, xvalclosest)))
            if self.Debug > 0: 
                print("xrngindex, rngidx[xrngindex] : " + str((xrngindex, rngidx[xrngindex])))
                print("rngidx["+str(xrngindex)+"], self.Xdata["+str(rngidx[xrngindex])+"]) : " + str((rngidx[xrngindex], self.Xdata[rngidx[xrngindex]])))
        
        # Arrange data in proper matrix
        # B = self.AnalyteYdata[rngidx[0]:rngidx[1]]  # [myFit(i).targets.ydata]    # I lineær algebra bogen er b det vi skal finde
        # Uh, bug: if you have a=[2,4,6,8,10] and do a[2] you get 6, but if you do a[0:2] you get [2,4].
        # --- i.e. a[start:end] end represents the index of the first item NOT to be included in the slice. This seems a bit non-pythonic to me...?
        B = np.array([analyteYdata[rngidx[0]:rngidx[1]+1] for analyteYdata in self.AnalyteYdata])
        A = np.array([pcYdata[rngidx[0]:rngidx[1]+1] for pcYdata in self.PcYdata])
        B = B.T # Think this needs to be transposed...
        A = A.T # Both needs to be transposed...
        xdataselection = self.Xdata[rngidx[0]:rngidx[1]+1]
        if self.Debug > self.DebugSilentLevel+1:
            print("doPcAnalysis() xdataselection :")
            print(np.array(xdataselection))
            print("doPcAnalysis A:")
            print(A)
            print("doPcAnalysis B:")
            print(B)
        #A = self.PcYdata[rngidx[0]:rngidx[1]] # [myFit(i).bases.ydata]      # ved brug af linearcombination af A's søjlevektorer
        # Least squares solution, cf Steven J Leon: Linear Algebra, p 237:
        # The equation system A x = b    (A matrix, x and b vectors) has unique least-square solution:
        #      x-hat = inv(A'*A)*A'*b    # Numpy: (A.T*A).I * A.T *
        # Using lstsq is more readable. linalg.solve is only when you have as many independent bases as you have unknowns.
        # In our case x is xdata (wavelength), b denotes ydata (absorbance) of a target/analyte. A contains y-data for the bases/principal components.
        # We can do this for multiple spectra (analytes/targets) using B = (b1,b2,...bn)
        # BACKGROUND subtraction: You may also want to add a constant function and e.g. a polynomial which can be used to background correct.
        
        (x, residues, rank, singulars) = np.linalg.lstsq(A, B)
        
        self.PcResult['PcCoeffs'] = x
        self.PcResult['A'] = A # Nice to have
        self.PcResult['B'] = B # Nice to have
        self.PcResult['ResidueSums'] = residues
        self.PcResult['Rank'] = rank
        self.PcResult['Singulars'] = singulars
        self.PcResult['Xdataselection'] = xdataselection
        C = np.dot(A, x)
        self.PcResult['C'] = C
        self.PcResult['Residuals'] = B - C
        # It might also be interesting to calculate using the full scale, not only the limits. But that can always be done as needed.
        if self.Debug-self.DebugSilentLevel > 1:
            print("doPcAnalysis() Principal coefficient matrix: ")
            print(x)
            print("doPcAnalysis() (residues, rank, singulars): ")
            print((residues, rank, singulars))
            print("doPcAnalysis() solution constructs, C ('projections / linear combinations'): ")
            print(C)
        elif self.Debug-self.DebugSilentLevel > 0:
            print("ComponentAnalyser.doPcAnalysis() > R-squared value(s) (1-residues):")
            print(1-residues)
            # Important note: NumPy array does not treat * as matrix-multiplication  (dot), but scalar. 
            # A*B will multiply every item of A with the corresponding of B.
            # To get A*x correct, use dot(A,x) or A.dot(x). Or let A be a NumPy-MATRIX rather than ARRAY (not recommended c.f. http://www.scipy.org/NumPy_for_Matlab_Users) 



    def plotPcResults(self, graphOptions=None):
        """graphOptions is a dict with graph options. 
        In original makeFitAndPlot I used a graph object to toss around, but this is 
        probably a bit more easy to understand...
        You should also refer to the scipy-plotter scripts, DataPlotter.py (newer) and FluoromaxDataPlotter.py (original)
        Note that these were more intended towards batch plotting of a large number of single files.
        Litt: http://www.scipy.org/Plotting_Tutorial and http://matplotlib.org/"""
        
        # First, produce the component reconstruction using pc result data:
        
        for i, ydata in enumerate(self.PcYdata):
            lbl = 'Pc'+str(self.Parameters['PcDataLines'][i])+': '+self.PcLabels[i]
            mpl.pyplot.plot(self.Xdata, ydata, label=lbl)
        for i, ydata in enumerate(self.AnalyteYdata):
            lbl = 'B-'+str(self.Parameters['AnalyteDataLines'][i])+': '+self.AnalyteLabels[i]
            mpl.pyplot.plot(self.Xdata, ydata, label=lbl)

        # Consider using zip rather than enumerate looping.
        for i, ydata in enumerate(self.PcResult['C'].T): # Note that we transpose to get one solution per row (and not column)
            lbl = 'C-'+str(self.Parameters['AnalyteDataLines'][i])+'='
            lbl += "+".join(['{0:.2F}xPc{1}'.format(*pair) for pair in zip(self.PcResult['PcCoeffs'].T[i], self.Parameters['PcDataLines']) ])
            lbl += ", R2={0:.3F}".format(1-self.PcResult['ResidueSums'][i])
            # Note how we transpose the coefficients to get row-wise. Alternatively, use [:,i] indexing.
            # Also note the use of * in *pair to unpackage the pair tuple. format expects unpackaged items. You can use ** to unpackage dicts to keyword arguments.
            # You could also use vformat rather than format, as detailed in http://docs.python.org/2/library/string.html
            # Could use {0:+.3g}, but the small '-' makes it look silly with current legend font. Types e.g.: G, F, f, g
            # Plot v1: Plot only in the x-range selected for analysis:
            mpl.pyplot.plot(self.PcResult['Xdataselection'], ydata, label=lbl)
            
        #Produce legend labels: self.PcLabels and self.AnalyteLabels plus the linear combinated reconstructs C.
        # Edit: Is done as we plot each dataseries.
        
        # Add the last finish to the plot:
        mpl.pyplot.ylabel('AU/mm')
        mpl.pyplot.xlabel('nm')
        mpl.pyplot.xlim(220, 450)
        mpl.pyplot.ylim(-0.05, 1.6)
        mpl.pyplot.legend(loc='upper right')
        mpl.pyplot.show()




if __name__ == "__main__":
    
    import argparse
    argparser = argparse.ArgumentParser(description='Reads spectrograms...')
    argparser.add_argument('-v', '--verbosity', action='count', default=0, help="Debug level. Use -vv to increase to level 2." )
    argparser.add_argument('files', nargs='?', help="ndj files to read..." )
    argparser.add_argument('-c', '--paramfile', help="Parameters file. Defaults to ComponentAnalyser.yaml")
    args = argparser.parse_args()
    if args.verbosity: debug = args.verbosity
    else: debug = 0
    if args.paramfile: 
        paramfile = args.paramfile
    else: 
        paramfile = 'ComponentAnalyser.yaml'

    # Simply setting a paramFile will load it automatically.
    ca = ComponentAnalyser(debug=debug, paramFile=paramfile)


    printParametersHelp = False
    if printParametersHelp:
        if 'Parameters Help' in ca.Parameters:
            print("Parameters Help: (parameters are stored in YAML file {}".format(paramfile))
            print(ca.Parameters['Parameters Help'])
    else:
        print("(parameters help is stored in parameter-file)")


    ca.readData()
    ca.doPcAnalysis() # Using analysisRange from self.Parameters
    ca.plotPcResults()




#   defaultYamlParams, can be imported with a=yaml.load(defaultYamlParams), then saved with yaml.dump(a, file)
    defaultYamlParams = """
Parameters Help: |
  Xdataline : Define the line in the NDJ file that includes the X-data (and other headers/fields).
  PcDataLines/AnalyteDataLines : List of lines defining lines in the NDJ file with Principal Components / Analytes, respectively.
  AnalysisRange, PlotRange (xmin, xmax): What range to plot. Use None for no limit (full range)

AnalysisRange: [270, 300]
AnalyteDataLines: [16]
PcDataLines: [10]
PlotRange: [null, null]
Xdataline: 5
"""







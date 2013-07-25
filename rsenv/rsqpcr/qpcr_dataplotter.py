# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 10:04:36 2013

@author: scholer

This program is used to process and plot qPCR data from e.g. the LightCycler480.

General usage scheme is as follows:
- Read Cp data for each position from qPCR datafile. 
- Read information about which samples are in which wells from a samplelist_ext_with_pos file.
- Read a samplelist_order file to determine which samples to plot and in which order.

The samplelist files may be conveniently produced using the SampleNameManager class.

"""




import numpy as np # use as np.arange(...)
from matplotlib import pyplot # use as pyplot.scatter(...)
import operator
from collections import OrderedDict
import random

from rsenv.rsqpcr.qpcr_datamanager import DataManager




class DataPlotter():
    
    def __init__(self):
        
        self.Prefs = dict()
        self.Datamanager = DataManager() 
        
        # Default plotting format:
        self.Yrange = ymin, ymax = 0, 40
        self.Plotsize = (12,7) #None # (width,height)
        # Larger figure sizes require larger fonts and wider lines.
        # Bitmap files will increase with size, while pdf and other vector formats are invariant to size.
        # Setting matplotlib.rcParams['figure.figsize'] = 5, 10 has been reported to be more portable.
        self.Figure_dpi = 300 # Doesn't seem to have any effect when saving as pdf or png, always 100 for png.
        self.Xticklabels = None
        self.Usehatch = True
        self.Plots = list() # list of plots
        # Default font seems to be VeraSans-Roman.
        self.Fontprops = dict(family='sans-serif', # can also be a font name.
                    )
        self.Xlabelprops = dict(self.Fontprops, # Adopt general prefs
                           fontsize='medium', #can also be in points. from xx-small over medium to xx-large
                           weight='medium', # 0-1000,‘ultralight’,‘light’,‘normal’,‘regular’,‘book’,‘medium’,‘roman’,‘semibold’,‘demibold’,‘demi’,‘bold’,‘heavy’,‘extra bold’,‘black’
                           rotation=80, rotation_mode='anchor',
                           verticalalignment='center', ha='right'
                           )
        self.Barprops = dict(
                    color='silver', width = 0.8, edgecolor='black', ecolor='k',
                    align='center', alpha=1, zorder=1, linewidth=1.5,
                    antialiased=True
        )
        # Make default hatch (also works as an example of use)
        # Hatch_prepend: Make sure to use this hatch pattern first:
        self.Hatch_prepend = ['/','xxx','\\xx','\\x','-xx','\\\\','/\\x','//','//\\']        
        # Produce a pseudo-random hatchpattern, prepended by 
        # example hatch_groupstructure = [5,4,2,7] (Repeat first hatch 5 times, second hatch four times, etc.)
        #self.Hatch_pat = self.makehatchpat(useextra=False,groups=None,prepend_pat=hatch_prepend)
    
    
    def applyFigureFormats(self, **kwargs):
        

        xticklabels = kwargs.get('xticklabels', self.Xticklabels)
        if xticklabels:
            pyplot.xticks(*zip(*enumerate(xticklabels)), **self.Xlabelprops)
            pyplot.xlim(-1,len(xticklabels))            
        figure_dpi = kwargs.get('dpi', self.Figure_dpi)
        if 'dpi' in kwargs:
            pyplot.gcf().set_dpi(figure_dpi)  # Doesn't seem to have any effect when saving as pdf or png, always 100 for png.
        plotsize = kwargs.get('plotsize', self.Plotsize)
        if plotsize:
            pyplot.gcf().set_size_inches(plotsize, forward=True)
        yrange = kwargs.get('yrange', self.Yrange)
        if yrange:
            pyplot.ylim(yrange)
        
        pyplot.tight_layout()
    
    """ ------- Plotting replicate-processed data : -------- """
    
    def plotbarsreplicateprocessedv3(self, data=None, barprops=None, hatch_pat=None):
        """
        RP = replicate processed, i.e. a mean has been calculated from the (biological) replicates.
        Note: Sample replicate vs (technical replicates = multiple measurements on the same sample)
        """
        if data is None:
            data = self.Datamanager.DataStruct
        if barprops is None:
            barprops = self.Barprops
        if hatch_pat is None and self.Usehatch:
            if self.Hatch_pat is None:
                self.makehatchpat()
            hatch_pat = self.Hatch_pat
        # This thows a warning because I try to take the average of an empty sequence
    #   cpmeans_techrep = OrderedDict([ (samplename, OrderedDict([ (replicateno, np.mean(replicate_cpvals)) for replicateno,replicate_cpvals in sampledata.items() ]) ) for samplename,sampledata in data.items() ])
        cpmeans_techrep = OrderedDict([ (samplename, [np.mean(replicate_cpvals) for replicate_cpvals in sampledata.values()] ) for samplename,sampledata in data.items() ])
        cpstdev_techrep = OrderedDict([ (samplename, [ np.std(replicate_cpvals) for replicate_cpvals in sampledata.values()] ) for samplename,sampledata in data.items() ])
    #    cpstdev_techrep = OrderedDict([(samplename, OrderedDict([ (replicateno, np.std(replicate_cpvals)) for replicateno,replicate_cpvals in sampledata.items() ]) ) for samplename,sampledata in data.items()])
        #print "der"
        cpmeans_replicate = OrderedDict( (samplename, np.mean(cpmeans_techrep)) for samplename,cpmeans_techrep in cpmeans_techrep.items() )
        print cpmeans_replicate
        cpstdev_replicate = OrderedDict( (samplename, np.std(cpmeans_techrep)) for samplename,cpmeans_techrep in cpmeans_techrep.items() )
        #print "joe"
        #print cpmeans
        #print cpstdev
        ind = np.arange(len(cpmeans_replicate))
        #ind = [i-barwidth/2 for i in np.arange(len(samplenames))]
        barprops["yerr"] = cpstdev_replicate.values()
        barplot = pyplot.bar(ind, cpmeans_replicate.values(), **barprops)
        # pyplot.bar() Return value is a list of matplotlib.patches.Rectangle instances.
        if hatch_pat:
            for bar,pat in zip(barplot, hatch_pat*5): 
                # *5 to make sure you have enough patterns.
                bar.set_hatch(pat) 
        self.Plots.append(barplot)
        return barplot



    """ ------- Plotting flat data : -------- """
    
    def plotIndividualFlat(self, data):
        """ datastructure v1: """
        #xyvalsv1cp = [(xpos,measurement["Cp"]) for xpos,sample in enumerate(data) for measurement in sample["qpcrdata"]]
    
        """ Datastructure v3 : """
        # xy, plotting all points, with with biological replicates side by side (not combined)
        #xyvalsv3flat = [(xpos,cp) for samplename,sampledata in data.items() for xpos,replicatedata in enumerate(sampledata) for cp in replicatedata]
        xyvalsv3flat = list() # So close that I could make a list comprehension, but the xpos was tricky.
        xpos = 0
        print data
        for samplename,sampledata in data.items():
            print "samplename, sampledata: {}, {}".format(samplename, sampledata)
            for replicateno,replicatedata in sampledata.items(): # edit: I'm using a sorted ordereddict now, so no need to constantly sort the replicates.
                for cp in replicatedata:
                    xyvalsv3flat.append((xpos, cp))
                xpos += 1 # this should be equal to sampleno+replicateno, which could be used to make a list comprehension.
    
        xyvals = xyvalsv3flat
        samplenames = data.keys() # the nice thing about having an ordereddict :-)
    
        # Muhahah, using zip unpacking :D
        # When you only have two replicates and you are using ddof=0 (default), then the two points are THE SAME as the STD bars.
        # In that case, no reason to plot...
        scatterprops = dict(s=1, c='k', marker='d', zorder=100)
        p1 = pyplot.scatter(*zip(*xyvals), **scatterprops)
        return p1
    
    def plotbarsv1(self, data, samplenames):
        barwidth = 0.8
        ind = np.arange(len(samplenames)) # can be used if you use align='center'
        #ind = [i-barwidth/2 for i in np.arange(len(samplenames))]
        barprops = dict(yerr = [sample["qpcrstd"] for sample in data], 
                    color='y', width = barwidth, edgecolor='k', ecolor='k',
                    align='center', alpha=0.5, zorder=1
                    )
        p2 = pyplot.bar(ind, [sample["qpcrmean"] for sample in data], **barprops)
        return p2
    
    def plotbarsflatv3(self, data):
        barwidth = 0.8
        #ind = np.arange(len(samplenames)) # can be used if you use align='center'
        # This thows a warning because I try to take the average of an empty sequence
        cpmeans = OrderedDict([(samplename+" #{}".format(replicateno), np.mean(replicate_cpvals) ) for samplename,sampledata in data.items() for replicateno,replicate_cpvals in sampledata.items()])
        cpstdev = OrderedDict([(samplename+" #{}".format(replicateno), np.std(replicate_cpvals) ) for samplename,sampledata in data.items() for replicateno,replicate_cpvals in sampledata.items()])

        ind = np.arange(len(cpmeans))
        #ind = [i-barwidth/2 for i in np.arange(len(samplenames))]
        barprops = dict(yerr = cpstdev.values(), 
                    color='y', width = barwidth, edgecolor='k', ecolor='k',
                    align='center', alpha=0.5, zorder=1
                    )
        p2 = pyplot.bar(ind, cpmeans.values(), **barprops)
        return p2
    
    
    
    
    """------------------------------------
    --- ARTISTIC THINGS -------------------
    ------------------------------------"""
    
    def makehatchpat(self, useextra=False, groups=None, prepend_pat=None):
        hatch1 = ['/', '-', 'x', '\\', '+'] # I do not use '|', it looks weird on vertical bars.
        hatchextra = ['.','*','o','0']   # http://matplotlib.org/api/artist_api.html#matplotlib.patches.Patch.set_hatch
        hatchextra = ['.'] # They all look weird.
        if prepend_pat is None:
            prepend_pat = list()
        # Sorting for easy removal of duplicates on set formation.
        hatch2 = ["".join(sorted(h1+h2)) for h1 in hatch1 for h2 in hatch1]
        hatch3 = ["".join(sorted(h1+h2+h3)) for h1 in hatch1 for h2 in hatch1 for h3 in hatch1]
        # if there are more than 
        if useextra:
            hatch2e = [h1+h2+h3 for h1 in hatch1 for h2 in hatch1 for h3 in hatchextra]
            hatch3e = [h1+h2+h3+h4 for h1 in hatch1 for h2 in hatch1 for h3 in hatch1 for h4 in hatchextra]
            # I only want to use a random subset of the extras:
            #import random
            random.shuffle(hatch2e)
            hatch2e=hatch2e[:len(hatch2e)/2]
            random.shuffle(hatch3e)
            hatch3e=hatch3e[:len(hatch3e)/3]
        else:
            hatch2e=hatch3e=[]
        # Exclude asymetric hatches (personal preference...)
        hatch_excludes = ['+']
        for h in hatch2+hatch3+hatch2e+hatch3e:
            if h in prepend_pat:
                hatch_excludes.append(h)
            if '+' in h and len(h)<3 and h.count('+') < 2:
                print "Excluding pattern: "+h
                hatch_excludes.append(h)
            if any(x in h for x in '-+'):
                #if h.count('\\') != h.count('/'):
                # Actually, even if there are the same number of \ and /, then there will also be one with x that is the same.
                # So, just dont mix -+ with /\.
                if '\\' in h or '/' in h:
                    hatch_excludes.append(h)
    
        hatch3e = list(set(hatch3e))
        #hatch_pat = ('/', '-', 'x', '\\', '++', '//', 'xx', '\\\\', '-/', '--', 'xxx', '///', 'xx-', '\\-/')
        # Make sure to exclude prepend_pat patterns.
        hatch_pat = list(set(hatch1+hatch2+hatch3+hatch2e+hatch3e)-set(hatch_excludes)-set(sorted(prepend_pat))) # also add semi-randomization...
        random.shuffle(hatch_pat) # further randomization...
        hatch_pat = prepend_pat + hatch_pat
        #hatch_pat = [h*i for h in hatch1 for i in range(1,7)] # To test how hatches look... 
        if groups is not None:
            hatch_pat_groups = list()
            for hidx,groupsize in enumerate(groups):
                for i in range(groupsize):
                    hatch_pat_groups.append(hatch_pat[hidx])
            hatch_pat_groups = [hatch_pat[hidx] for hidx,groupsize in enumerate(groups) for i in range(groupsize)]
            hatch_pat = hatch_pat_groups
        self.Hatch_pat = hatch_pat
        return hatch_pat
    


#####################################################
##### Plotting refs, tips and tricks ################
#####################################################


# Other stackoverflow examples:
# http://stackoverflow.com/questions/6352740/matplotlib-label-each-bin
# http://stackoverflow.com/questions/10998621/rotate-axis-text-in-python-matplotlib - uses matplotlib.rc and rotation=45
# http://stackoverflow.com/questions/6541123/improve-subplot-size-spacing-with-many-subplots-in-matplotlib



# Wow, by the way: http://detexify.kirelabs.org/classify.html
# Converts a drawed input to latex character.


# Regarding figure sizes and dpi:
# http://stackoverflow.com/questions/10118523/matplotlib-savefig-dpi-setting-is-ignored
# http://stackoverflow.com/questions/332289/how-do-you-change-the-size-of-figures-drawn-with-matplotlib
# http://matplotlib.org/users/customizing.html # INCL how to set rc values
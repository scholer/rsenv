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
import matplotlib.lines
import matplotlib.patches
import matplotlib.text
import matplotlib
import operator
from collections import OrderedDict
import random
import logging
logger = logging.getLogger(__name__)

from rsenv.rsqpcr.qpcr_datamanager import DataManager
from rsenv.rsqpcr.rscolormanager import StyleManager


class DataPlotter():

    def __init__(self):

        self.Prefs = dict()
        self.Datamanager = DataManager()
        self.Pickerartistbroker = dict()
        # Default plotting format:
        self.Yrange = ymin, ymax = 0, 40
        self.StyleManager = StyleManager()
        self.Stdcurve_colors = self.StyleManager.Colors
        self.Plotsize = (12,7) #None # (width,height)
        # Larger figure sizes require larger fonts and wider lines.
        # Bitmap files will increase with size, while pdf and other vector formats are invariant to size.
        # Setting matplotlib.rcParams['figure.figsize'] = 5, 10 has been reported to be more portable.
        self.Figure_dpi = 300 # Doesn't seem to have any effect when saving as pdf or png, always 100 for png.
        self.Xticklabels = None
        self.Usehatch = True and False
        self.Plots = list() # list of plots
        # markers: '.' = dot, 'D' = diamond, ',' = pixel, '+', 'o', '*', 'x', 'h', '^'
        # pixel does not seem affected by markersize.
        # linestyles: '-'=solid, '--'=dashed, ':'=dotted, 'None'
        # linestyle marker is overruled by the presence of a marker.
        # color: rgbcmyk, or a valid html color name.
        self.Pointprops = dict(color='black', marker='.', linestyle='None', markersize=3)
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
        # Ok, 1.2.1 also does not support 'fontsize', requires 'size'
        #if matplotlib.__version__.split('.') < ['1','2','0']:
        if matplotlib.__version__.split('.') < ['1','2','2']:
            # For old legacy matplotlib versions:
            self.Legendprops = dict(size='x-small', weight='medium') # changed fontsize to size.
        else:
            self.Legendprops = dict(fontsize='x-small', weight='medium')
        # Make default hatch (also works as an example of use)
        # Hatch_prepend: Make sure to use this hatch pattern first:
        self.Hatch_pat = None
        self.Hatch_prepend = ['/','xxx','\\xx','\\x','-xx','\\\\','/\\x','//','//\\']
        # Produce a pseudo-random hatchpattern, prepended by
        # example hatch_groupstructure = [5,4,2,7] (Repeat first hatch 5 times, second hatch four times, etc.)
        #self.Hatch_pat = self.makehatchpat(useextra=False,groups=None,prepend_pat=hatch_prepend)


    def applyFigureFormats(self, axis=None, **kwargs):
        """
        http://matplotlib.org/api/axes_api.html vs http://matplotlib.org/api/pyplot_api.html
        """
        xticklabels = kwargs.get('xticklabels', self.Xticklabels)
        if axis is None:
            axis = pyplot.gca()
            # note: replacing 'axis' and 'pyplot' in code below:
        pyplot.axes(axis) # make 'axis' the current axis.
        if xticklabels:
            #print 'xticklabels:'
            #print xticklabels
            #print '--'
            pyplot.xticks(*zip(*enumerate(xticklabels)), **self.Xlabelprops)
            pyplot.xlim(-1,len(xticklabels))
            #axis.set_xticklabels(*zip(*enumerate(xticklabels)), **self.Xlabelprops) # set_xticks is only for numeric values (tick positions)
            #axis.set_xlim(-1,len(xticklabels))
        figure_dpi = kwargs.get('dpi', self.Figure_dpi)
        if 'dpi' in kwargs:
            pyplot.gcf().set_dpi(figure_dpi)  # Doesn't seem to have any effect when saving as pdf or png, always 100 for png.
        plotsize = kwargs.get('plotsize', self.Plotsize)
        if plotsize:
            pyplot.gcf().set_size_inches(plotsize, forward=True)
        yrange = kwargs.get('yrange', self.Yrange)
        if yrange:
            #pyplot.ylim(yrange)
            axis.set_ylim(yrange)

        pyplot.tight_layout()


    def getRecentPlot(self):
        return pyplot.gcf()



    """ ------- Plotting replicate-processed data : -------- """

    def plotbarsreplicateprocessedv3(self, data=None, barprops=None, hatch_pat=None, axis=None):
        """
        RP = replicate processed, i.e. a mean has been calculated from the (biological) replicates.
        Note: Sample replicate vs (technical replicates = multiple measurements on the same sample)
        axis: the pyplot axis to use for plotting. If None, call pyplot.gca().
        """
        logger.info("\n>>>>> Initiating plotbarsreplicateprocessedv3 >>>>>>")
        if data is None:
            data = self.Datamanager.DataStruct
        if barprops is None:
            barprops = self.Barprops
        if hatch_pat is None and self.Usehatch:
            if self.Hatch_pat is None:
                self.makehatchpat()
            hatch_pat = self.Hatch_pat
        if axis is None:
            axis = pyplot.gca()
        # This thows a warning because I try to take the average of an empty sequence
        #cpmeans_techrep = OrderedDict([ (samplename, OrderedDict([ (replicateno, np.mean(replicate_cpvals)) for replicateno,replicate_cpvals in sampledata.items() ]) ) for samplename,sampledata in data.items() ])
        logger.info("calculating cpmeans_techrep")
        cpmeans_techrep = OrderedDict([ (samplename, [np.mean(replicate_cpvals) for replicate_cpvals in sampledata.values()] ) for samplename,sampledata in data.items() ])
        logger.info("calculating cpstdev_techrep")
        cpstdev_techrep = OrderedDict([ (samplename, [ np.std(replicate_cpvals) for replicate_cpvals in sampledata.values()] ) for samplename,sampledata in data.items() ])
        #cpstdev_techrep = OrderedDict([(samplename, OrderedDict([ (replicateno, np.std(replicate_cpvals)) for replicateno,replicate_cpvals in sampledata.items() ]) ) for samplename,sampledata in data.items()])
        #print "der"
        logger.info("calculating cpmeans_replicate")
        cpmeans_replicate = OrderedDict( (samplename, np.mean(cpmeans_techrep)) for samplename,cpmeans_techrep in cpmeans_techrep.items() )
        logger.info("calculating cpstdev_replicate")
        cpstdev_replicate = OrderedDict( (samplename, np.std(cpmeans_techrep)) for samplename,cpmeans_techrep in cpmeans_techrep.items() )

        ind = np.arange(len(cpmeans_replicate))
        #ind = [i-barwidth/2 for i in np.arange(len(samplenames))]
        barprops["yerr"] = cpstdev_replicate.values()
        logger.info("Plotting barplot (replicateprocessed v3)")
        barplot = axis.bar(ind, cpmeans_replicate.values(), **barprops)
        # pyplot.bar() Return value is a list of matplotlib.patches.Rectangle instances.
        logger.info("Making hatcing pattern:")
        if hatch_pat:
            for bar,pat in zip(barplot, hatch_pat*5):
                # *5 to make sure you have enough patterns.
                bar.set_hatch(pat)
        self.Plots.append(barplot)
        logger.info("<<< plotbarsreplicateprocessedv3 completed <<<< \n")
        return barplot


    def plotpoints(self, data=None, plotprops=None, foreach='sample', replicateshift=0.05):
        """
        foreach: 'sample' or 'replicate'; 'sample' plots all measurements for each sample together.
        replicateshift: how much to shift replicates for each sample.
        """
        if data is None:
            data = self.Datamanager.DataStruct
        if plotprops is None:
            plotprops = self.Pointprops
            print "Point plot props: {}".format(plotprops)
        for sampleindex, (samplename, sampledata) in enumerate(data.items()):
            print "{}, '{}' : {}".format(sampleindex, samplename, ", ".join(["{}".format(lst) for lst in sampledata.values()]) )
        # sampledata is currently an OrderedDict, *not* just a list;
        xyvals = [ (sampleindex+replicateshift*(replicateindex-0.5*len(sampledata)),   measurement) \
            for sampleindex, (samplename, sampledata) in enumerate(data.items()) \
                for replicateindex, replicatemeasurements in enumerate(sampledata.values()) \
                    for measurement in replicatemeasurements ]
#        print 'xyvals:'
#        print xyvals
#        print 'zipped:'
#        print zip(*xyvals)
        #yvals =
        #xvals =
        xvals, yvals = zip(*xyvals)
        #plot = self.getRecentPlot()
        pyplot.plot(xvals, yvals, **plotprops)



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
        print "plotbarsflatv3: Calculating cp means:"
        cpmeans = OrderedDict([(samplename+" #{}".format(replicateno), np.mean(replicate_cpvals) ) for samplename,sampledata in data.items() for replicateno,replicate_cpvals in sampledata.items()])
        print "plotbarsflatv3: Calculating cpstdev:"
        cpstdev = OrderedDict([(samplename+" #{}".format(replicateno), np.std(replicate_cpvals) ) for samplename,sampledata in data.items() for replicateno,replicate_cpvals in sampledata.items()])

        ind = np.arange(len(cpmeans))
        #ind = [i-barwidth/2 for i in np.arange(len(samplenames))]
        print "plotbarsflatv3: Plotting bars:"
        barprops = dict(yerr = cpstdev.values(),
                    color='y', width = barwidth, edgecolor='k', ecolor='k',
                    align='center', alpha=0.5, zorder=1
                    )
        print "plotbarsflatv3: Plotting points:"
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


    def plot_stdcurves_fromsamplename_regex(self, regexlist, curvenames):
        curvedata = self.Datamanager.generateStdCurveFromRegexNamed(regexlist, curvenames, doprint=True)
        for curvename,stdcurvedata in curvedata.items():
            if len(stdcurvedata) < 1:
                continue
            print 'stdcurvedata 11:'
            print stdcurvedata
            x_repmeans = [ (entry[0], [np.mean(repdata) for repindex,repdata in entry[1].items()]) for entry in stdcurvedata]
            print 'x_repmeans 22: '
            print x_repmeans
            data_processed = [ (entry[0], np.mean(entry[1]), np.std(entry[1]) ) for entry in x_repmeans]
            print 'data_processed 33:'
            print data_processed
            #conc, ctmean, cterr = zip(*data_processed)
            #print conc, ctmean, cterr
            xvals, yvals = zip(*[ (entry[0], yval) for entry in x_repmeans for yval in entry[1]] )
            print 'xvals:'
            print xvals
            print 'yvals:'
            print yvals
            pyplot.semilogx(xvals, yvals, hold=True, marker='*', label=curvename)
            pyplot.legend() # make legend using existing lines...
#            pyplot.plot(conc, ctmean) #, yerr=cterr)


    def plotstdcurves(self, regexlist, curvenames, makelegend=True, stdcurveaxis=None, residualsplotaxis=None):
        """
        If stdcurveaxis is provided, the standard curves will be plotted on this axis.
        Residuals are only plotted if residualsplotaxis is provided.
        Convenience 'standard' is allowed.
        """
        colors = self.Stdcurve_colors
        if 'standard' in (stdcurveaxis, residualsplotaxis):
            # call signature is subplot2grid( (total_rows, total_cols), (row_index, col_inxex), rowspan=N, colspan=N)
            # note that indices are 0-based.
            stdcurveaxis = pyplot.subplot2grid( (1,2), (0,0) )
            residualsplotaxis = pyplot.subplot2grid( (1,2), (0,1) )
        elif stdcurveaxis is None:
            stdcurveaxis = pyplot.gca()
        stdcurves_info = self.Datamanager.stdcurveAutomator(regexlist, curvenames, VERBOSE=0)
        curvecolors = dict( zip(stdcurves_info['qrmean_data'].keys(), colors*5) )
        print 'curvecolors:\n'+'\n'.join(["{}: {}".format(name, color) for name, color in curvecolors.items() ])
        # plot datapoints:
        for stdcurvename, stdcurve_qrmean_data in stdcurves_info['qrmean_data'].items():
            points = [ (datapoint[0], ct_qrmean_val) for datapoint in stdcurve_qrmean_data for ct_qrmean_val in datapoint[1] ]
            if len(points) < 1:
                continue
            # points = list of (x,y) tuples
            xvals,yvals = zip(*points)
            #print "plotting with xvals: {}, yvals: {}, stdcurvename: {}".format(xvals, yvals, stdcurvename)
            #stdcurveaxis.semilogx(xvals, yvals, '*', color=curvecolors[stdcurvename], label=stdcurvename) #marker='*', linestyle=None,
            #print "'{}' curve plotted.".format(stdcurvename)
        # plot linear fit points:
        print "\nPlotting linear fit points::"
        for stdcurvename, fitpointsvals in stdcurves_info['linfitpoints'].items():
            #points = [ (datapoint[0], ct_qrmean_val) for datapoint in stdcurve_qrmean_data for ct_qrmean_val in datapoint[1] ]
            # points = list of (x,y) tuples
            xvals,yvals,ymeans,yresiduals,yerr = zip(*fitpointsvals)
            stdcurveaxis.semilogx(xvals, yvals, linestyle=':', color=curvecolors[stdcurvename], marker=None)#, label="linfit of {}".format(stdcurvename) )
            print "xvals: {}".format(xvals)
            print "yvals: {}".format(yvals)
            print "ymeans: {}".format(ymeans)
            print "yresiduals: {}".format(yresiduals)
            print "yerr: {}".format(yerr)

            stdcurveaxis.errorbar(xvals, ymeans, yerr=yerr, linestyle='None', color=curvecolors[stdcurvename], marker='*', label=stdcurvename)
            xlim = residualsplotaxis.get_xlim()
            stdcurveaxis.set_xlim(xlim[0]*0.9, xlim[1]*1.1)
            if residualsplotaxis:
                print 'Plotting residuals for {} curve'.format(stdcurvename)
                print 'yresiduals: {}'.format(yresiduals)
                # uh... is yerr only available in barplots and errorplot?
                # see http://matplotlib.org/api/pyplot_api.html#matplotlib.pyplot.errorbar
                # for log, search for 'scale' (linear or log) - you can use the set_xscale() method of an axis object :)
#                residualsplotaxis.semilogx(xvals, yresiduals, ':*', yerr=yerr, color=curvecolors[stdcurvename], label="{} fit residuals".format(stdcurvename) )
#                residualsplotaxis.set_xscale('log')
                residualsplotaxis.errorbar(xvals, yresiduals, yerr=yerr, markersize=4, linestyle=':', color=curvecolors[stdcurvename], label="{} residuals".format(stdcurvename) )
                residualsplotaxis.axhline(color='k')
                xlim = residualsplotaxis.get_xlim()
                residualsplotaxis.set_xlim(xlim[0]*0.9, xlim[1]*1.1)

        if makelegend:
            # Notice: fontsize and other properties not supported in all versions of matplotlib!
            # If you receive an error, comment out.
            stdcurveaxis.legend(prop=self.Legendprops)
            #stdcurveaxis.legend()
            if residualsplotaxis:
                residualsplotaxis.legend(prop=self.Legendprops)
                # Specifying fontsize seems to not be supported (at least in my matplotlib, which is only 1.1.1)
                #- although according to http://matplotlib.org/api/axes_api.html it should be!
        print "\nStandard curve stats:"
        for stdcurvename, fitdata in stdcurves_info['linfits'].items():
            print "{name}: R2={r_squared:.3f}, Eff={eff:.3f}, Slope={slope:.2f}, Intercept={intercept:.1f}".format(
                    name=stdcurvename, r_squared=fitdata[2]**2, slope=fitdata[0], intercept=fitdata[1],
                    eff=stdcurves_info['pcr_efficiencies'][stdcurvename])
#        self.plot_stdcurves_fromsamplename_regex(regexlist, curvenames)


    def plotCycledata(self, cycledata=None, ax=None, picker=True, yscale=None, xscale=None):
        """
        Cycledata datastructure is:
            datastruct[key samplename][key replicateno][key qpcr_pos][list index] = (cycle, fluorescenceval)

        """
        if cycledata is None:
            cycledata = self.DataManager.Rawcycledatastruct
        if cycledata is None or len(cycledata) < 1:
            print "No cycledata..."
            return
        if ax is None:
            fig = pyplot.figure()
            ax = pyplot.gca()
        plts = list()
        legend_plts = list()
        legend_labels = list()
        print "Input cycledata: {}".format(type(cycledata))
        for samplename, samplereplicates in cycledata.items():
            (switched, (color, linestyle, marker)) = self.StyleManager.switchStyle(new=samplename)
            for replicateno, qpcr_replicates in samplereplicates.items():
                for qpcr_pos, well_cycledata in qpcr_replicates.items():
                    label = "{samplename},{replicateno} ({pos})".format(pos=qpcr_pos, samplename=samplename, replicateno=replicateno)
                    #print "pos: {pos}, samplename: {samplename}, replicateno: {replicateno}".format(pos=qpcr_pos, samplename=samplename, replicateno=replicateno)
                    # notice the (plt, ) unpacking; plot() returns a *list* of 'matplotlib.lines.Line2D' instances.
                    plt, = pyplot.plot(*zip(*well_cycledata), picker=picker, marker=marker, color=color, ls=linestyle,
                        label=label )
                    plts.append(plt)
            if switched:
                print "Adding label: {}".format(label)
                legend_plts.append(plt)
                legend_labels.append(label)
            else:
                print "NOT adding label: {}".format(label)
        if yscale:
            ax.set_yscale(yscale)
        if xscale:
            ax.set_xscale(xscale)
        if picker:
            pyplot.gcf().canvas.mpl_connect('pick_event', self.onpick1)

        return ax, plts, legend_plts, legend_labels


    def onpick1(self, event):
        """
        from http://matplotlib.org/examples/event_handling/pick_event_demo.html
        http://wiki.scipy.org/Cookbook/Matplotlib/Interactive_Plotting
        http://matplotlib.org/users/recipes.html
        """
        broker = self.Pickerartistbroker.setdefault(type(event.artist), list())
        try:
            lastartist = broker.pop()
        except IndexError:
            lastartist = None
        broker.append(event.artist)
        if isinstance(event.artist, matplotlib.lines.Line2D):
            thisline = event.artist
            xdata = thisline.get_xdata()
            ydata = thisline.get_ydata()
            label = thisline.get_label()
            thisline.set_lw(thisline.get_lw()+1)
            if lastartist:
                lastartist.set_lw(lastartist.get_lw()-1)
            ind = event.ind
            # np.take is basically just object-independent index-based addressing
            # label is str instance.
            print 'onpick1 line: {} at (x,y)=({}, {})'.format(label, np.take(xdata, ind), np.take(ydata, ind))
        elif isinstance(event.artist, matplotlib.patches.Rectangle):
            patch = event.artist
            print('onpick1 patch:', patch.get_path())
        elif isinstance(event.artist, matplotlib.text.Text):
            text = event.artist
            print('onpick1 text:', text.get_text())





if __name__ == '__main__':

    # set up:
    #import os
    import time
    startclock = time.clock()
    dp = DataPlotter()
    def testStdcurvePlotting():
        sampledatayaml = 'sampledata/RS157b_qPCR_datastruct.yml' ##os.path.curdir
        dp.Datamanager.loadfromyaml(sampledatayaml)
        xticklabels = dp.Datamanager.DataStruct.keys()
        # (rows, cols)
    #    ax1 = pyplot.subplot2grid( (2,3), (0,0), colspan=2, rowspan=2 )
    #    ax2 = pyplot.subplot2grid( (2,3), (0,2) )
    #    ax3 = pyplot.subplot2grid( (2,3), (1,2) )
        ax1 = pyplot.subplot2grid( (2,2), (0,0), colspan=1, rowspan=2 )
        ax2 = pyplot.subplot2grid( (2,2), (0,1) )
        ax3 = pyplot.subplot2grid( (2,2), (1,1) )
        # http://matplotlib.org/users/gridspec.html
        # see also matplotlib.figure.Figure.add_subplot(...)
        # http://matplotlib.org/api/figure_api.html
        # http://matplotlib.org/api/pyplot_api.html
        # http://matplotlib.org/api/axes_api.html

        # testing plots:
        dp.plotbarsreplicateprocessedv3(axis=ax1)
        dp.applyFigureFormats(axis=ax1, xticklabels=xticklabels)

        dp.plotpoints()

        # testing standard curve plots:
        regexlist = ['(\d.*\d) vs Dzol 30 min', '(\d.*\d) active', '(\d.*\d) inactive', '^(\d.*\d)\W*$']
        curvenames = ['Dzol 30 min', 'active', 'inactive', 'non-purified calibration']
        dp.plotstdcurves(regexlist, curvenames, stdcurveaxis=ax2, residualsplotaxis=ax3)

        pyplot.show()


    def testCycledataPlotting():
        cycledatafn = 'sampledata/20130904 wp test.txt'
        sampleposmap = dp.Datamanager.SampleNameManager.makeEmptyFullPosMap(ncols=5, saveToSelf=False)
        print "Empty sampleposmap generated... ({})".format(time.clock()-startclock)
        data = dp.Datamanager.makeRawcycledatastructure(cycledatafn, sampleposmap)
        print "Cycledata datastruct generated... ({})".format(time.clock()-startclock)
        dp.plotCycledata(data)
        "Dataplotter: cycledata plotted, showing plot figure ({})".format(time.clock()-startclock)
        pyplot.show()

    testCycledataPlotting()

    print "Dataplotter: MAIN/TEST RUN FINISHED... ({})".format(time.clock()-startclock)


#####################################################
##### Plotting refs, tips and tricks ################
#####################################################


# Other stackoverflow examples:
# http://stackoverflow.com/questions/6352740/matplotlib-label-each-bin
# http://stackoverflow.com/questions/10998621/rotate-axis-text-in-python-matplotlib - uses matplotlib.rc and rotation=45
# http://stackoverflow.com/questions/6541123/improve-subplot-size-spacing-with-many-subplots-in-matplotlib



# Regarding linear fits:
# http://glowingpython.blogspot.it/2011/07/polynomial-curve-fitting.html
# http://glowingpython.blogspot.dk/2012/03/linear-regression-with-numpy.html
# http://sdtidbits.blogspot.dk/2009/03/curve-fitting-and-plotting-in-python.html
# http://stackoverflow.com/questions/893657/how-do-i-calculate-r-squared-using-python-and-numpy
# http://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.lstsq.html?highlight=residuals

# http://glowingpython.blogspot.dk/2011/04/how-to-plot-function-using-matplotlib.html



# Wow, by the way: http://detexify.kirelabs.org/classify.html
# Converts a drawed input to latex character.


# Regarding figure sizes and dpi:
# http://stackoverflow.com/questions/10118523/matplotlib-savefig-dpi-setting-is-ignored
# http://stackoverflow.com/questions/332289/how-do-you-change-the-size-of-figures-drawn-with-matplotlib
# http://matplotlib.org/users/customizing.html # INCL how to set rc values

# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 09:18:06 2013

Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com

@author: scholer
"""

import numpy as np # use as np.arange(...)
try:
    import scipy.stats
    scipy_available = True
except ImportError, e:
    print "Notice: SciPy not available.{}".format(e)
    scipy_available = False
import math
from matplotlib import pyplot # use as pyplot.scatter(...)
import operator
from collections import OrderedDict
import random
import yaml

from rsenv.rsqpcr.qpcr_samplemanager import SampleNameManager


class DataManager():
    def __init__(self):
        self.Prefs = dict(qpcr_no_signal_cp_value=40,
                          saveDatastructureYamlFile=None)
        self.SampleNameManager = SampleNameManager()
        self.StructureVersion = None
        self.DataStruct = None
        self.Rawcycledatastruct = None
        self.Cpdata = None
        self.Metadata = None




    ###############################
    ## LOADING AND SAVING DATA ####
    ###############################

    def readCpDatafile(self, cpdatafile, qpcr_no_signal_cp_value=None):
        if qpcr_no_signal_cp_value is None:
            qpcr_no_signal_cp_value=self.Prefs["qpcr_no_signal_cp_value"]
        with open(cpdatafile) as f:
            cp_metadata = f.readline()
            cpheader = f.readline().strip().split('\t')
            # edit: instead of having a list of lists, I change so I have a list of dicts.
            cpdata = [dict(zip(cpheader, line.strip().split('\t'))) for line in f if line.strip()[0] != "#"]
        # cast all cp data to float:
        for entry in cpdata:
            try:
                # for some reason using entry.get("Cp", qpcr_no_signal_cp_value)) yielded all empty Cp fields
                entry["Cp"] = float(entry["Cp"]) if entry["Cp"] else qpcr_no_signal_cp_value
            except ValueError, e:
                print e
                print "entry: {}, cp: '{}'".format(entry, entry.get("Cp", qpcr_no_signal_cp_value))
        self.Cpdata = cpdata
        self.Metadata = cp_metadata
        return cpdata, cp_metadata

    def readCycledatatxtfile(self, datafn):
        """ generator, yielding a data dict for every data entry in datafn cycledata txt file.
        """
        with open(datafn) as f:
            expmetadata = f.readline() # first line is metadata
            fields = f.readline().strip().split('\t')
            for line in f:
                yield dict(zip(fields, line.strip().split('\t')))


    def loadfromyaml(self, yamlfilename):
        with open(yamlfilename) as f:
            self.DataStruct = yaml.load(f)

    def savetoyaml(self, yamlfilename):
        with open(yamlfilename, 'wb') as f:
            yaml.dump(self.DataStruct, f)



    ############################
    ## CONVENIENCE METHODS: ####
    ############################

    def makeSampleNamePosMap(self, sampleposfile):
        return self.SampleNameManager.makeSampleNamePosMap(sampleposfile)
    def getSamplePosMap(self):
        return self.SampleNameManager.SamplePosMap




    def makeSamplenameFromFullsamplestring(self, samplenamefull):
        """
        logic to convert a full sample string to a sample name.
        """
        sampleparams = samplenamefull.split(",")
        try:
            replicateno = int(sampleparams[-1].split("#")[-1])
            # Sample name is samplenamefull.split(",")[:-1]
            samplename = ",".join(sampleparams[:-1])
        except ValueError:
            #print "makeDatastructureV4fromPos(): ValueError, could not extract replicateno from samplename '{}'".format(samplenamefull)
            replicateno = 1
            samplename = ",".join(sampleparams)
        return samplename, replicateno





    """"-------------------------------------------------------------
    ----  DATA STRUCTURES -------------------------------------------
    --------------------------------------------------------------"""

    def makeRawcycledatastructure(self, cycledatafn=None, sampleposmap=None, cyclingprogno='2', 
                usePosAsSampleName=False, VERBOSE=2):
        """
        Datastructure is:
            datastruct[key samplename][key replicateno][key qpcr_pos][list index] = (cycle, fluorescenceval)
        Generation is quite computational heavy, since it does not use the line order of the data.
        This means that things like replicateno, etc are computed for each entry, not just every block.
        Edit, optimization: only change list and generate new samplename and replicateno if pos is different 
        from last line. This reduced datastruct generation from 3.5 secs to 0.7 ! (of which 0.43 is used
        on reading the cycledatafile (generator).
        Edit, optimization: Added cyclingprogno option, only entries with this Prog# will be included.
            This reduces generation time by 0.05 secs, and reduces memory consumption. And makes downstream
            processing easier.
        Inputdata (txt format) fields:
            SamplePos : Well position (384-wp format)
            SampleName : Well samplename
            Prog# : 1=?, 2=PCR Cycling; 3=Melting profile,
            Seg#  : Unknown, but seems to always be '3'.
            Cycle#: Cycle number in pcr cycling, starts at '1'.
            Time : Time, currently unknown format (probably seconds or something)
            Temp : Measuring temperature.
            465-510 : Fluorescence from this laser/filter combination.
        """

        if cycledatafn is None:
            cycledatafn = self.Cycledatafile
        if sampleposmap is None:
            sampleposmap = self.getSamplePosMap()
        if not (cycledatafn and sampleposmap):
            raise ValueError("Missing cpdata or sampleposmap.")

        datastructurev3minimal = OrderedDict() 
        datastruct = datastructurev3minimal
        currentpos = 'None'
        for entry in self.readCycledatatxtfile(cycledatafn):
            if entry['Prog#'] != cyclingprogno and cyclingprogno is not None:
                continue
            pos = entry['SamplePos']
            if pos != currentpos:
                try:
                    samplenamefull = sampleposmap[pos]
                except KeyError:
                    if VERBOSE > 2:
                        print "makeDatastructureV(): KeyError, no sample found for pos {} (probably just an empty well)".format(pos)
                    if usePosAsSampleName:
                        if VERBOSE > 2:
                            print "Using samplenamefull = pos"
                        samplenamefull = pos
                    else:
                        continue
                if samplenamefull == 'None':
                    # None is used as a filler during sample-name generation (typically only needed for Anders' non-sequential plate layout...)
                    continue
                samplename, replicateno = self.makeSamplenameFromFullsamplestring(samplenamefull)
                """datastruct[key samplename][key replicateno][key qpcr_pos] = (cycle, fluorescenceval)"""
                currentlist = datastruct.setdefault(samplename, OrderedDict()).setdefault(replicateno, dict()).setdefault(pos, list())
                currentpos = pos
            currentlist.append( (int(entry['Cycle#']), float(entry['465-510'])) )

        self.Rawcycledatastruct = datastruct
        return datastruct


    """ --- DATASTRUCTURE v3 minimal, ordereddict grouped by sample replicates --- """
    
    def makeDatastructureV3minimal(self, cpdata=None, sampleposmap=None):
        """
Used from: RS155
Here I read the cpdata list of dicts and use the cpdata[i]["Pos"] via sampleposmap to group.
Edit: this was supposed to be for datastructurev3, but I will give v3minimal a shot. 
v3minimal uses an ordereddict, since I would otherwise need to search datastructurev3[i]["samplename"], 
to see if a samplename was already present in the datastructure, which got kind of akward...
Using dicts make this much more elegant using the setdefault method.

datastructurev3minimal:
  OrderedDict
    [<samplename>]: dict # originally intended as a list, but index-testing got akward.
      [<replicateno>]: list
        [<qpcr_tech_rep>]: <cp value>
Regarding sorting a dict on the fly:
sort dict d by value: sorted(d.items(), key=operator.itemgetter(1)) -- or sorted(d, d.get) if you only want to have the keys sorted by value.
sort dict d by key:   sorted(d.items()) as sorted will sort first by the first element in the key-val tuple.
 --- to store as a dict (and not tuple): OrderedDict(sorted(d.items()))
        """
        if cpdata is None:
            cpdata = self.Cpdata
        if sampleposmap is None:
            sampleposmap = self.SampleNameManager.SamplePosMap
        if not (cpdata and sampleposmap):
            raise ValueError("Missing cpdata or sampleposmap.")
        datastructurev3minimal = OrderedDict() #list()
        for entry in cpdata:
            cpval = entry["Cp"]
            pos = entry["Pos"]
            try:
                samplenamefull = sampleposmap[pos]
            except KeyError:
                print "makeDatastructureV(): KeyError, no sample found for pos {} (probably just an empty well)".format(pos)
                continue
            if samplenamefull == 'None':
                # None is used as a filler during sample-name generation (typically only needed for Anders' non-sequential plate layout...)
                continue
            samplename, replicateno = self.makeSamplenameFromFullsamplestring(samplenamefull)
            if cpval < 1:
                # I might exclude undetected measurements, so I do not add their cp value, but I still need to make sure there is an entry to avoid keyerrors.
                datastructurev3minimal.setdefault(samplename, OrderedDict()).setdefault(replicateno, list())
            else:
                datastructurev3minimal.setdefault(samplename, OrderedDict()).setdefault(replicateno, list()).append(cpval)
        
        self.StructureVersion = "V3minimal"
        self.DataStruct = datastructurev3minimal
        return datastructurev3minimal


    """ --- V3minimal was used to be called v4, I think: --- """
    def makeDatastructureV4fromPos(self, cpdata, sampleposmap):
        return self.makeDatastructureV3minimal()

    """ --- Data structure V2: as dict: {samplename:[qpcr-replicates]} --- """
    """ --> Abandoned. """
    # simple grouping, by samplename, in a dict {samplename:<samplelist>}
    # note: zip, izip and friends produces tuples; that might not be desired...
    #cpdatagen = (entry for entry in cpdata)
    #tech_rep = 2 # technical replicates: (2 = duplicates, etc) 
    # not using itertools.izip_longest right now...
    #data_grouped_simple = dict(zip(samplenames, zip(*[(e for e in cpdata)]*tech_rep)))
    # longer, using for loops:
    #data_grouped_v2 = dict()
    #for samplename in samplenames:
    #    data_grouped_v2[samplename] = qpcrdata = list()
    #    for i in range(tech_rep):
    #        qpcrdata.append(cpdatagen.next())
    



    """ --- Data structure as list: [{samplename:<name>,qpcrdata:[<qpcrdata>]}] --- """
    # Ok, going all-in with the data-as-a-dict had one major shortcoming:
    # All the data that is not easily grouped by samplename, but where it is much easier to refer
    # to them as a sequence, e.g. all control samples and standards.
    # V1-type datastructure:
    def makeFlatSampleDataFromSequence(self, samplenames, cpdatasequence, tech_rep):
        data = list()
        #nentries = 0
        for samplename in samplenames:
            qpcrdata = list()
            data.append({"samplename":samplename, "qpcrdata":qpcrdata})
            for i in range(tech_rep):
                qpcrdata.append(cpdatasequence.next())
        if len(samplenames) != len(data):
            print "WARNING: len(samplenames) =! len(data)  -- ({} vs {})".format(len(samplenames),len(data))
    
        """ --- Calculating mean and stdev --- """
        print "Mean, STD - Samplename"
        for sample in data:
            cpvals =  [measurement["Cp"] for measurement in sample["qpcrdata"] ]
            sample["qpcrmean"] = np.mean( cpvals )
            sample["qpcrstd"] = np.std( cpvals, dtype=np.float64)#,ddof=1)
            print "{0}, {1} - {2}".format(sample["qpcrmean"], sample["qpcrstd"], sample["samplename"])
        return data




    """ -------- GROUPING DATA  v2.2   -----------------"""
    # alternative, based on itertools.groupby() - never implemented,
    # should probably not be implemented as a static transformation of data,
    # but rather produce a dynamic structure per request.











    """--------------------------------------------------------------
       ----------- DATA SORTING AND FILTERING -----------------------
       --------------------------------------------------------------"""


    """-- DATA SORTING and FILTERING for v3-type datastructure  -------"""

    def filterDataV3(self, data):
        return data
    
    def sortDataV3(self, data):
        return data
    
    def dataByList(self, sampleorder, data=None, persist=True):
        """ Sometimes it is just easier to list them in the order you want,
            rather than rely on some particular ordering mechanism.
            # dataByList also changes the format slightly, using an ordered dict for both
            # data[samplename] and data[samplename][replicateno]. 
            sampleorder: list or filename string.
        """
        if data is None:
            data = self.DataStruct
        if isinstance(sampleorder, basestring):
            with open(sampleorder) as f:
                order = [line.strip() for line in f if len(line) > 1 and line[0] != "#"]
            sampleorder = order
        print data.keys()
        print sampleorder
        databylist = OrderedDict([(samplename, OrderedDict(sorted(data[samplename].items())) ) for samplename in sampleorder])
        if persist:
            self.DataStruct = databylist
        return databylist


    """ -------- DATA SORTING and FILTERING FOR v1 DATASTRUCTURE ---"""
    # Params sorting and ad-hoc grouping:
    # Unless you have a lot of It is generally easier to simply use 
    # a file that lists which samples to plot and in what order.
    
    # LEGACY SORTER.
    def sortdatav1(self, data):
        def getparamsfromsamplename(samplename):
            #origamis, durations, exposures, precipmethods
            samplenameitems = ["origami", "duration", "exposure", "precipmethod"]
            paramsfromsamplename = dict(zip(samplenameitems, samplename.strip().split(', ')))
            return paramsfromsamplename
    
        def getfieldfromsamplename(field, samplename):
            paramsfromsamplename = getparamsfromsamplename(samplename)
            return paramsfromsamplename[field]
    
        mygraphsortorder = ["origami", "duration", "exposure", "precipmethod"] # How the samples are named:
        mygraphsortorder = ["duration", "precipmethod", "origami", "exposure"] # How the samples were made
        mygraphsortorder = ["precipmethod", "origami", "duration", "exposure"] # How I prefer to see the samples
        #mygraphsortorder = ["origami", "duration", "exposure", "precipmethod"] # Custom/adhoc
        # If you want non-alfabetical sorting, you need to make a dict-list:
        eachparamsortorder = {"origami":["PegTR","StdTR"],
                              "duration":["Non-incubated","Incubated"],
                              "exposure":["water","serum","blood-plasma","blood-cells"],
                              "precipmethod":["PEG precip.","DNAzol precip."]
                              }
        def myorderfunc(params):
            if isinstance(params, basestring):
                params = getparamsfromsamplename(params)
            # params should now be a dict.
            # when sorting a tuple, python first sorts by the first item, then the next, etc.
            #print "params: {}".format(params)
            return [eachparamsortorder[sortfield].index(params[sortfield]) 
                        if params[sortfield] in eachparamsortorder[sortfield]
                        else params[sortfield]
                    for sortfield in mygraphsortorder]
    
        def dictdataorderfun(entry):
            return myorderfunc(entry["samplename"])
    
        # Wow, this is vastly easier than the "calculate pos" alternative (my own self-made sorting logic...)
        # If something seems hard to do, it is probably not worth doing :p
        #print "data order before sort:"
        #print "\n".join(["{0:02} {1}".format(i,sample["samplename"]) for i,sample in enumerate(data)])
    
        return sorted(data[0:32], key=dictdataorderfun) + data[32:]

    """ ---- Filter v1-type data --- """
    def filter_data(self, data):
        drop_data_withpars = {"origami":[],
                              "duration":[],
                              "exposure":["blood-plasma","blood-cells"],
                              "precipmethod":["PEG precip."]
                              }
    
        print "N samples before filter: {}".format(len(data))
        samples_to_remove = list()
        for sample in data:
            act = "Skipping"
            #print "-\n"+sample['samplename']
            try:
                pars = getparamsfromsamplename(sample['samplename'])
            except:
                break
        #    print pars.items()
            #print pars.items()
            act = "Not removing"
            for p,v in pars.items():
                #print "p,v = {},{}".format(p,v)
                if v in drop_data_withpars[p]:
                    #print "removing sample {} in data: {}".format(sample['samplename'], sample in data)
                    # Wow, I think this is causing a bug: If you remove while iterating, then you skip.
                    samples_to_remove.append(sample)
                    #print "Param: {} = {} -- REMOVING SAMPLE".format(p,v)
                    act = "Removing"
                    break
                #else: 
                #    print "Param: {} = {} -- OK".format(p,v)
            
            #print "{} sample {} in data: {}".format(act, sample['samplename'], sample in data)
        #print "N samples after filter: {}".format(len(data))
        # If you remove while you loop, then you get a bug (it skips to the next), so doing it afterwards like this:
        for sample in samples_to_remove:
            data.remove(sample)
        print "N samples after filter: {}".format(len(data))
        return data


    ###############################
    ## Standard curve related: ####
    ###############################

    def generateStandardCurvesFromSamplenameRegex(self, regexlist, data=None, regexflagsum=0, VERBOSE=2):
        import re
        stdcurves_datastruct = list() #OrderedDict()
        if data is None:
            data = self.DataStruct
        for regex in regexlist:
            pat = re.compile(regex, regexflagsum)
            this_regex_data = list()
            for samplename, sampledata in data.items():
                match = pat.match(samplename)
                if match:
                    xval = match.groups()[0].replace('10^', '1e')
                    try:
                        xval = float(xval)
                    except ValueError, e:
                        print "Could not convert conc value: {}".format(e)
                    this_regex_data.append( (xval, sampledata) )
                    # also: match.groupdict() returns dict.
                    if VERBOSE > 1:
                        print "'{}' MATCHED '{}' <---".format(regex, samplename)
                else:
                    if VERBOSE > 2:
                        print "'{}' did not match '{}'".format(regex, samplename)
            stdcurves_datastruct.append(this_regex_data) # list of (conc,[replicate ct vals])
        return stdcurves_datastruct


    def generateStdCurveFromRegexNamed(self, regexlist, curvenames, doprint=False, data=None, regexflagsum=0, VERBOSE=0):
        """
Standard curve rawdatastruct:
OrderedDict: str <curve name> : list <curve data> 
<curve data>: list of two-tuples -> ( float <conc>, OrderedDict <ct datastruct> )
<ct datastruct>: biorep_index : list <qpcr replicate measurements for biological replicate>

# qrmean = mean of qpcr replicate measurements for a biological sample replicate
Standard curve qrmean datastruct: stdcurve_qrmean_data
OrderedDict: str <curve name> : list <curve data> 
<curve data>: list of two-tuples -> ( float <conc>, list <qrmean values> )
<ct datastruct>: biorep_index : list <qpcr replicate measurements for biological replicate>

        """
        stdcurvedata = self.generateStandardCurvesFromSamplenameRegex(regexlist, data, regexflagsum, VERBOSE)
        if doprint:
            for i, regexdata in enumerate(stdcurvedata):
                print "'{}' curve:".format(curvenames[i])
                print "conc\tyvals:"
                # e, E, f, F, g, G, %
                # e = always exponential, f = always fixed point, g = exponential or fixed.
                print "\n".join([ "{:.3g}\t{}".format(conc, ", ".join(["{}".format(lst) for lst in sampledata.values()]) ) for conc, sampledata in regexdata] )
        curvedata = dict([ (curvenames[i], regexdata) for i, regexdata in enumerate(stdcurvedata)  ])
        return curvedata


    def calculateStdCurveQrmean(self, stdcurve_rawdata):
        def mymean(vals):
            print vals
            return np.mean(vals)
        stdcurve_qrmean_data = OrderedDict()
        for curvename,curvedata in stdcurve_rawdata.items():
            #print curvedata
            stdcurve_qrmean_data[curvename] = [ (c[0], map(np.mean, c[1].values() )) for c in curvedata ]
        return stdcurve_qrmean_data


    def generateLogLinStdCurveData(self, stdcurve_qrmean_data, reverse=False, base=10):
        #logfuns = {'10':np.log10, '2':np.log2, 'e':np.log)
        #log = logfuns[str(logbase)]
        if reverse:
            if base in ('e', 'natural'):
                log = np.math.exp
            else:
                log = lambda x: np.math.pow(base, x)
        else:
            if base in ('e', 'natural'):
                log = np.math.log
            else:
                log = lambda x: math.log(x, base)
        logdata = OrderedDict()
        for curvename,curvedata in stdcurve_qrmean_data.items():
            logdata[curvename] = [(log(c[0]), c[1]) for c in curvedata]
        return logdata

    def generateLinearFits(self, stdcurve_qrmean_data, VERBOSE=0):
        """
        Expecting a stdcurve_qrmean_data like construct.
        Returns a similar construct: stdcurve_linfits

        Two options:
        1) Use np.linalg.lstsq(A, y)   -- returns least square solution to Ax = y equation system.
        2) Use np.polyfit(x, y, 1)     -- returns coefficients for 1-degree polynomial. 
           - Use np.poly1d(coeffs) to get a polynomial functions for calculating y-values for fit.
        3) Use scipy.stats.linregress(x, y)
           - This has the advantage of returning correlation coefficient, eliminating the roundtrip to np.corrcoef.
           - It is ok to just do: r_squared = r_value**2.

        np.linalg.lstsq returns: coefficients, residues, rank, 

        Refs:
        1) http://glowingpython.blogspot.dk/2012/03/linear-regression-with-numpy.html
        2) http://glowingpython.blogspot.it/2011/07/polynomial-curve-fitting.html
           http://sdtidbits.blogspot.dk/2009/03/curve-fitting-and-plotting-in-python.html
        """
        linfitdata = OrderedDict()
        for curvename,curvedata in stdcurve_qrmean_data.items():
            data = [ (c[0], qrmean) for c in curvedata for qrmean in c[1]]
            if VERBOSE > 1:
                print data
            if len(data) < 1:
                continue
            linfitdata[curvename] = self.linregress( data )
            #linfitdata[curvename] = scipy.stats.linregress( [ (c[0], qrmean) for c in curvedata for qrmean in c[1]] )
        return linfitdata

    def linregress(self, data):
        xdata,ydata = zip(*data)
        if scipy_available:
            return scipy.stats.linregress( data )
        else:
            # method 1, polyfit:
            #fitres = np.polyfit(zip(*data), 1, full=True) # full=True also returns residuals, rank, etc.
            #coeffs, residuals = fitres[0:2]
            coeffs = np.polyfit(xdata, ydata, 1)
            
            # method 2, linalg.lstsq:
            # lstsq(A,y) solves the equation A*c = y; A*t = a1*c1+a0*c0 = y
            # with a1 being the 'x' vector and a0=(1,1,...), this is the same as x*c1+c0 = y.
            # lstsq returns: (coeffs, residues_sum, rank, singular_vals)
            #A = np.array([xdata, np.ones(len(xdata))]) 
            #fitres = np.linalg.lstsq(A.T, y)
            #coeffs = fitres[0]
            
            # Correlation:
            correlation = np.corrcoef(xdata, ydata)[0,1] # yes, ugly. corrcoef returns a matrix.
            # correlation is the same as r_value, and r_squared is really just the squared value.
            
            # return (slope, intercept, r-value), similarly to scipy.stats.linregress:
            return (coeffs[0], coeffs[1], correlation)


    def calcPcrEfficiencies(self, linfits, base=10):
        if base == 'e':
            fun = lambda x: math.exp(-x[0]**-1)-1
        else:
            fun = lambda x: math.pow(base, -x[0]**-1)-1
        effs = OrderedDict( [( curvename, fun(fitdata) ) for curvename, fitdata in linfits.items() ]  )
        return effs


    def calcLinRegPoints(self, linfits, stdcurve_qrmean_data=[0, 1e8], logbase=10, 
            semiloginput='NotImplemented', semilogoutput='NotImplemented', VERBOSE=0):
        """
        input data must be non-logarithmic conc values (xvalues);
        logbase is the base of the logarithm that was applied before making the linear regression fit.
        if logbase is set to None, then the input/output data will be semilog format.
        the stdcurve_qrmean_data is only used to generate data range and xvalues to calculate for.
        
        input stdcurve_qrmean_data must be either a tuple specifying (xmin, xmax), or a 
        stdcurve_qrmean_data datastruct where:
            stdcurve_qrmean_data[curvename] = [ float conc, ct_vals ]
            where ct_vals is list of sample replicate measurements at that concentration, like:
                [ (sample replicate 1 ct vals), (sample replicate 2 ct vals) ]
        
        input linfitdata must be either :
            dict-like,   linfitdata[curvename] = (SLOPE, INTERCEPT, ...)
            tuple-like,  linfitdata = (SLOPE, INTERCEPT, ...)
        
        Returns: dict[<stdcurvename>] = list of (xval, yfit, ymean, residual, yerr) points.
        Where   xvals = concentration for a point on the standard curve,
                yfit  = calculated ct value for the fitted standard curve
                ymean = ct mean values of biological sample replicates at that concentration. 
                        (which are calculated from the mean of the measured ct values of each qpcr technical replicate)
                residual = ymean-yfit
                yerr  = standard deviation for biological sample replicates.

        Code changes: 
            Changed from using a lot of zips of the data to just have a single for loop.
            This is much more readable.
        """
        if logbase is None:
            transform = lambda x: x
        elif logbase == 'e':
            transform = lambda x: math.log(x)
        else:
            transform = lambda x: math.log(x, logbase)#, x)
        # Trying to establish what range we should calculate curve points for:
        linregpoints = OrderedDict()
        def calc_yfit_tuple(a, b, xval, ymean, yerr):
            print "calculating tuple for conc point: {}, {}, {}".format(xval, ymean, yerr)
            yfit = a*transform(xval)+b
            residual = ymean-yfit if ymean else None
            return (xval, yfit, ymean, residual, yerr)
        def calc_yfit_tuple_multi(a, b, xval, ymean, yerr):
            print "calculating tuple for conc point: {}, {}, {}".format(xval, ymean, yerr)
            yfit = a*transform(xval)+b
            yerr = np.std(ymean)
            ymean = np.mean(ymean)
            residual = ymean-yfit
            return (xval, yfit, ymean, residual, yerr)
        try:
            # Test if stdcurve_qrmean_data is simply a tuple with (xmin, xmax):
            xmin = stdcurve_qrmean_data[0]
            xmax = stdcurve_qrmean_data[1]
            xvals = [np.linspace(xmin, xmax, num=20) for fit in linfits]
            try:
                for curvename, linfitdata in linfits.items():
                    a, b = linfitdata[0:2]
                    linregpoints[curvename] = [calc_yfit_tuple(a,b, xval, None, None) for xval in xvals]
            except Exception as e:
                print "calcLinRegPoints() :: Exception, perhaps you've provided linfits without the outer dict[curvename]=fitdata structure?"
                linregpoints = [calc_yfit_tuple(linfits[0], linfits[1], xval, None, None) for xval in xvals]
            return linregpoints
        except Exception as e:
            pass
            # Assume stdcurve_qrmean_data is the main datastructure, and linregpoints structure on this input:
        for curvename, curvedata in stdcurve_qrmean_data.items():
            a, b = linfits[curvename][0:2]
            linregpoints[curvename] = [calc_yfit_tuple_multi(a, b, concpointdata[0], concpointdata[1], None) for concpointdata in curvedata]
            if VERBOSE > 3:
                print "\ncalcLinRegPoints() :: Values for curve '{}':".format(curvename)
                print "\n".join( ["{:03g} : {}, {}, {}, {}".format(*point) for point in linregpoints[curvename] ])
                print "\n"
        return linregpoints



    def stdcurveAutomator(self, regexlist=None, curvenames=None, VERBOSE=0):
        if regexlist is None or curvenames is None:
            # self.Stdcurves_defs = (  (curve1name, curve1regex), ... )
            curvenames, regexlist = zip(*self.Stdcurves_defs) # <=> self.Stdcurves_defs = zip(curvenames, regexlist)
        stdcurve_rawdata = self.generateStdCurveFromRegexNamed(regexlist, curvenames, doprint=(VERBOSE>1), VERBOSE=VERBOSE)
        if VERBOSE > 2:
            print '\nstdcurve_rawdata:'
            print stdcurve_rawdata
        
        stdcurve_qrmean_data = self.calculateStdCurveQrmean(stdcurve_rawdata)
        if VERBOSE > 2 or True:
            print '\nstdcurve_qrmean_data:'
            print stdcurve_qrmean_data
        
        stdcurve_semilog_data = self.generateLogLinStdCurveData(stdcurve_qrmean_data)
        if VERBOSE > 2:
            print '\nstdcurve_semilog_data:'
            print stdcurve_semilog_data
        
        #scipy_available = False
        stdcurve_linfits = self.generateLinearFits(stdcurve_semilog_data)
        if VERBOSE > 2:
            print '\nstdcurve_linfits:'
            print stdcurve_linfits

        stdcurve_efficiencies = self.calcPcrEfficiencies(stdcurve_linfits)
        if VERBOSE > 2:
            print '\nstdcurve_linfits:'
            print "\n".join(["{}: {}".format(name, eff) for name, eff in stdcurve_efficiencies.items() ])

        stdcurve_linfitpoints = self.calcLinRegPoints(stdcurve_linfits, stdcurve_qrmean_data)
        # should be equivalent to:
        #stdcurve_linfitpoints = dm.calcLinRegPoints(stdcurve_linfits, [1e2,1e8])
        #stdcurve_linfitpoints = dm.calcLinRegPoints(stdcurve_linfits, stdcurve_semilog_data, logbase=None)
        # semilog in, semilog out; must either be plotted on axis with log(conc) on the x-axis, or transformed before plotting.
        if VERBOSE > 2 or True:
            print '\nstdcurve_linfitpoints:'
            print "\n".join(["{}: {}".format(name, points) for name, points in stdcurve_linfitpoints.items() ])

        # residual[curvename] = (concentration
        residuals = OrderedDict([ (curvename, 
            (concpoint[0], np.mean(concpoint[1]), np.std(concpoint[1]) ) )
            for curvename, concpoints in stdcurve_linfitpoints.items()
            for concpoint in concpoints])

        print "residuals: {}".format(residuals)

        return dict(qrmean_data=stdcurve_qrmean_data, 
                    linfits=stdcurve_linfits, 
                    linfitpoints=stdcurve_linfitpoints,
                    residuals=residuals,
                    pcr_efficiencies=stdcurve_efficiencies)





"""------------------------------------------------------
--- DATA STRUCTURE CONSIDERATIONS -----------------------
------------------------------------------------------"""

""" 

Currently used datastructure is: "datastructurev3minimal".
- produced by makeDatastructureV4fromPos() !

Alternative minimal datastructurev3minimal: 
-- however, this does not leave any place for derived data such as mean, stdev, etc.
-- but that can probably just as well be calculated on the fly, using map or some custom function...
datastructurev3minimal:
  OrderedDict[<samplename>]:
    list[<replicateno>]
      list[<qpcr_tech_rep>]
        <cp value>

Datastructure v3
Added sample replicate grouping in main data structure.
Datastructure is: 
 samples (list)
  [i] <sample> (dict)
    ["samplename"] string <samplename>
    ["cpdata"] (list/dict)
      [j] list of qpcr data for each sample replicate
        [k] float value of a qpcr measurement
    ["cpmean"] = derived cpmean value for all sample replicates
    ["cpstdev"] = derived cpstdev value for all sample replicates
Pipeline is:
1) Read extended sample list (1 entry per well/measurement)
2) 

New version v2:
Uses a grouped data-structure rather than flat-flat.
Primary grouped by: Tech replicates
(Will also add sample replicates when needed)

Secondarily can also be grouped by other parameters, in this case:
origami, exposure, time, and precipmethod.
Secondary grouping is done on-the fly; i.e. the data structure produced by 
the primary grouping is not permanently affected.

"""




# cpdata is still flat, same as the initial datafile.
# Now, do grouping:
# I wonder if it is best to keep as list, or tear down in favor of a dict, and then simply store 
# the original index as a field in the dict.? In that case, samplename could be the dict key.
# If I insist on grouping but keep as list, then I need to determine where to put the samplename.
# should it be as follows, with =[] indicating list, and ={} indicating dict, 0-> is used to 
# indicate list indices, while field: indicated dict keys:value pairs.
# data=[
# - 0->paramgroup1=[
# ---- 0->sample1[
# --------0->qpcr_replicate_1: {samplename:"samplename1", Cp:15.5, ...}
# or:
# data:
# - 0->paramgroup1
# -- -- 0->sample1{
# -------samplename:"samplename1"
# -------data:[
# ---------0->qpcr_replicate_1: {samplename:"samplename1", Cp:15.5, ...}
# data:
# - 0->paramgroup1
# --- 0->sample1
# ----- 0->sample1
# -------0->qpcr_replicate_1: {samplename:"samplename1", Cp:15.5, ...}
# alternatives, based on dicts:
# this alternative does 
# data={
# - {param1:val1,param2:val2,param3:val3}:paramgroup1={
#     "params":{paramsdict}
#     "samples":samplelist=[
#           0->sample1=[
# --      -----0->qpcr_replicate_1: {samplename:"samplename1", Cp:15.5, ...}




if __name__ == '__main__':
    
    import time
    
    # set up:
    #import os
    dm = DataManager()
    sampledatayaml = 'sampledata/RS157b_qPCR_datastruct.yml' ##os.path.curdir
    cycledatafn = 'sampledata/20130904 wp test.txt'
    sampleposmap = dm.SampleNameManager.makeEmptyFullPosMap(saveToSelf=False)
    
    #dm.loadfromyaml(sampledatayaml)
    
    # tests:
    # regex tests:
    regexlist = ['(\d.*\d) vs Dzol 30 min', '(\d.*\d) active', '(\d.*\d) inactive', '^(\d.*\d)\W*$']
    curvenames = ['Dzol 30 min', 'active', 'inactive', 'non-purified calibration']
    #stdcurves_info = dm.stdcurveAutomator(regexlist, curvenames, VERBOSE=0)
    #print '\n\nstdcurves_info:'
    #print stdcurves_info
#    stdcurve_rawdata = dm.generateStdCurveFromRegexNamed(regexlist, curvenames, doprint=True, VERBOSE=2)
#    print '\nstdcurve_rawdata:'
#    print stdcurve_rawdata
#    
#    stdcurve_qrmean_data = dm.calculateStdCurveQrmean(stdcurve_rawdata)
#    print '\nstdcurve_qrmean_data:'
#    print stdcurve_qrmean_data
#    
#    stdcurve_semilog_data = dm.generateLogLinStdCurveData(stdcurve_qrmean_data)
#    print '\nstdcurve_semilog_data:'
#    print stdcurve_semilog_data
#    
#    #scipy_available = False
#    stdcurve_linfits = dm.generateLinearFits(stdcurve_semilog_data)
#    print '\nstdcurve_linfits:'
#    print stdcurve_linfits

#    stdcurve_efficiencies = dm.calcPcrEfficiencies(stdcurve_linfits)
#    print '\nstdcurve_linfits:'
#    print "\n".join(["{}: {}".format(name, eff) for name, eff in stdcurve_efficiencies.items() ])

#    stdcurve_linfitpoints = dm.calcLinRegPoints(stdcurve_linfits, stdcurve_qrmean_data)
#    # should be equivalent to:
#    #stdcurve_linfitpoints = dm.calcLinRegPoints(stdcurve_linfits, [1e2,1e8])
#    #stdcurve_linfitpoints = dm.calcLinRegPoints(stdcurve_linfits, stdcurve_semilog_data, logbase=None)
#    # semilog in, semilog out; must either be plotted on axis with log(conc) on the x-axis, or transformed before plotting.
#    print '\nstdcurve_linfitpoints:'
#    print "\n".join(["{}: {}".format(name, points) for name, points in stdcurve_linfitpoints.items() ])



    # Testing cycledata parsing:
    test_loop_count = 0
    start = time.clock()
    for entry in dm.readCycledatatxtfile(cycledatafn):
#        print "\n".join("{}: ")
        #print entry
        if test_loop_count:
            break
    elapsed = (time.clock() - start)
    print "Cycledata generator forloop time: {}".format(elapsed)
    # Testing cycledata datastruct generation:
    start = time.clock()
    cycledatastruct = dm.makeRawcycledatastructure(cycledatafn, sampleposmap)
    elapsed = (time.clock() - start)
    print "Cycledata datastruct generation time: {}".format(elapsed)



    # obs: ^ is Bitwise Exclusive Or operator in Python !
#    print stdcurvedata






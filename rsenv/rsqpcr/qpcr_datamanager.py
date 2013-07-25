# -*- coding: utf-8 -*-
"""
Created on Wed Jul 24 09:18:06 2013

Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com

@author: scholer
"""

import numpy as np # use as np.arange(...)
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
        return self.SampleNameManager.SampleNamePosMap



    """"-------------------------------------------------------------
    ----  DATA STRUCTURES -------------------------------------------
    --------------------------------------------------------------"""



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
            sampleparams = samplenamefull.split(",")
            try:
                replicateno = int(sampleparams[-1].split("#")[-1])
                # Sample name is samplenamefull.split(",")[:-1]
                samplename = ",".join(sampleparams[:-1])
            except ValueError:
                #print "makeDatastructureV4fromPos(): ValueError, could not extract replicateno from samplename '{}'".format(samplenamefull)
                replicateno = 1
                samplename = ",".join(sampleparams)
            if cpval < 1:
                # I exclude undetected measurements, so I do not add their cp value, but I still need to make sure there is an entry to avoid keyerrors.
                datastructurev3minimal.setdefault(samplename, dict()).setdefault(replicateno, list())
            else:
                datastructurev3minimal.setdefault(samplename, dict()).setdefault(replicateno, list()).append(cpval)
        
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









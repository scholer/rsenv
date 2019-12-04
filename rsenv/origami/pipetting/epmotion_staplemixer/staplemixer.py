#!/usr/bin/env python
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
# pylint: disable-msg=W0621
"""
About:
Staplemixer may be used as a quick tool to combine information from a
cadnano design with information on oligo plates and yield a method
file that can be loaded into the epmotion robot.

General workflow:
1) Use automapper on your exported staple-list (*.csv) to produce a *.smmc file
2) Use epmotion_staplemixer to produce a robot method file (*.dws) file by combining
   the *.smmc file with rack/plate information lists (*.rack.csv files).

Quick start guide:
automapper.py is found in oligomanager/tools/file_transformations/, and
epmotion_staplemixer.py is found in oligomanager/epmotion_staplemixer/ -- but I recommend making
a symlink to these (named automapper and epmotion_staplemixer) and put these somewhere
in your local $PATH$, e.g. ~/bin
Navigate to the directory where you have your design. Copy the *.rack.csv files
for the oligo racks/plates that you want to use, making them if neccesary.
Also place *.colormap and *.seqmap files here for automapper.
Run the commands:
    automapper <staple-list>.csv
    epmotion_staplemixer

Yes, epmotion_staplemixer does not currently take any arguments. Configuration is done
with either a yaml file or by editing epmotion_staplemixer.py and/or ConfigGenerator.py


Using automapper, details:
First, you should use automapper.py to produce a smmc file, where:
 - All '?'-bases have been mapped to proper (ATGC) bases (seqmap).
 - All colors (#3377ff) have been mapped to a modulename (colormap), optional.
Then you need to place the oligo plate/rack information as csv/tdl.
Plates should be specified with one csv file per plate, with the fields:
    Sequence, Pos

Using epmotion_staplemixer, details:
The epmotion_staplemixer script is currently (2012) programmed to automatically find
the files it needs. It does not take any commandline arguments.
(Yaml-based configuration is not fully tested, but should be fairly straight-
forward, as long as the yaml data looks like the data from ConfigGenerator).

Staplemixer function, detailed:
The main loop runs:
StapleMixer:generateInstructionCsv()
1) read design file (the first file named "*.smmc")
2) reads plate files (named ".rack.csv")
3) create pipet data
4) write pipet data to file `"sm-"+self.RunDateHourStr+".pip.csv"`
StapleMixer:generateRobotFile(fromfiles=False)
1) Reads pip.csv file (if not handed directly)
2) Write instructions to .dws file
   - All written instructions are template-based; just fills in blanks with format()
   - Pipet instructions are passed through pipetinstructionToCmdVars(instruction)
     to convert the pipet data into a dict ready for format()


StapleMixer vs main OligoManager:
# Original oligomanager2 would handle all method formatting in EpMotion module.
# oligomanager does not use a "cmd-template" but writes cmd options one-by-one
    by handing a dict to a specialized writer method.
# Staplemixer is created to be a light-weight alternative that allows faster
    output, providing configuration only by editing text-files. No GUI.
    Generally, the user should not be required to run anything but
    automapper and then epmotion_staplemixer to get a robot instructions file.



How to improve this program:
1) Config should be in yaml file. Or at least, the robot part.
    Remember that most user-specified formatting is lost when saving yaml files.
    This includes dict order, etc.
2) Get rid of "insertPlaceholders". It only causes trouble. Instead, merge a
    "constant" dict with each pipet-instruction, e.g. do
    robotfile.write(self.Config["robot"]["cmd-template"] % instruction.update(constantdict))
    # Note however that this will overwrite pipet dict with constantdict values if keys are present.
    # It might be better to do constantdict.update(instruction),
    # but make sure you update a *copy* of the constantdict not the main constantdict!


## TODO:
## - Get out of the "global config" paradigm. It doesn't work.
## --> ALTERNATIVELY: Have ConfigGenerator set all dynamic values.
       You could also use ConfigGenerator to load any robot.yml files.
       You could even use ConfigGenrator to specify which labware to use.
       In this case, insertPlaceholders method should be moved to ConfigGenerator.
       But still, get away from a global config.
       Perhaps store config parameters in a .cfgpars file if needed.
       (This would basically just be self.Config["output"] )
       Status: I have removed everything but "robot" from self.Config.
## - Option to use the "pool from one location" epmotion command.


Remember to refer to oligomanager/oligomanager/biz/EpMotion.py for labware info.

# Changelog:
## - DONE: Test with epMotion. (Anne-Louise's designs)
## - FIXED: Truncate destposnames in the dws file! (Software only support up to 20 chars)
## - FIXED: TransferVolumeNanoliter was decimal formatted, 5000.0, not integer.
## - DONE, New feature: Support for a "modules-to-pipet" file, in which you can define which modules to pipette and how much.
## - DONE, New Feature: Export the modules used to a csv file (which can be easily imported to excel and then printed with brother label maker)
    - Fixed a lot of stuff to make it actually work...
    - Added UserIntervention after placeit cmds.
 ## - Adding racknames to the workspace (Place It cmds)  (DONE)
 ## - Intelligent filling of workspace (first add racks, then tips)
        Ok, using ntipracks in range(len(pipetdataset)/96+1) to estimate number of tip-racks needed.
## - Support for YAML-based configuration. - DONE.
## Support for --modulenameprefix cmdline argument.

"""

import sys
import csv
import os
import glob
import operator
from datetime import datetime
import io
from collections import OrderedDict
#try:
#    import simplejson as json
#except ImportError:
#    import json
# I'm not using json format at the moment, I prefer yaml.
import yaml
#from ConfigGenerator import ConfigGenerator
#from pprint import pprint
import logging
logger = logging.getLogger(__name__)

if __package__ is None or __name__ is '__main__':
    import sys
    fp = os.path.abspath(os.path.realpath(__file__))
    print("__file__ = %s" % fp)
    packagedir = os.path.dirname(os.path.dirname(fp))
    print("Adding dir to sys.path: %s" % packagedir)
    sys.path.append(packagedir)
    # Note: The above does not always work, e.g. for py2exe or other environments.
    # Alternatives, to obtain dir/path of executable:
    # http://stackoverflow.com/questions/2632199/how-do-i-get-the-path-of-the-current-executed-file-in-python
    # Alternative A: to get
    # import inspect
    # os.path.abspath(inspect.getsourcefile(lambda _: None))


from rsenv.origami.oligomanager_lib.filedatalib import fileutils
from rsenv.origami.oligomanager_lib.oligodatalib.plateutils import indexToPos, indexToRowColTup, posToRowColTup
from .epmotionvalet import EpmotionValet


class StapleMixer(object):
    """
    ## Input files: designfilename (*.csv.smmc),
                    staple-rack-oligos ("*.rack.csv")
                    modulestopipet list (*.modulestopipet)
    ## Output files:
                    sm-yyyymmdd-HHMM.pip.csv,
                    sm-yyyymmdd-HHMM.dws
    """
    def __init__(self, robotcmdtemplatefile="epmotion-cmd-templates.yml", rackfilenames=None,
                 usefiltertips=True, modulenameprefix=""):
        self.Rundatetime = datetime.now()
        self.Usefiltertips = 1 if usefiltertips else 0
        self.Modulenameprefix = modulenameprefix
        self.InsertPlaceholderCount = 0 # Keep track of how many times you have used insertPlaceholders() method.
        self.RunDateHourStr = self.Rundatetime.strftime("%y%m%d-%H%M")
        # After loading the config, I do % configpars mod to it to replace named placeholders.
        self.PipDataFields = ["row", "source-rackname", "source-pos", "destin-rackname", "destin-index", "volume", "cmd-comment"]
        self.Robotcmdtemplatefile = robotcmdtemplatefile
        self.Resuspend_maxvol = 900
        # Configpars is used as an initial formatter. Values that I do not want to set
        # initially should be marked with "field":"%(field)s" in that way, another
        # placeholder is just inserted. Note that this is really tricky with
        # fields that are not strings, e.g. 03d formatted fields.
        # Honestly, it is probably easier to not fiddle around like this and only
        # use insertPlaceholders() once!
        # Edit: I do not use insertPlaceholders when I create e.g. cmd-transfer commands. I just do <template> % <vars-dict>
        # Pipet file defines: row,source-rackname,source-pos,destin-rackname,destin-index,volume,cmd-comment
        self.Configpars = { # Remember that if you do string formatting and do not provide all placeholders, you will get a KeyError.
            "filename": "sm-"+self.RunDateHourStr+".dws",
            "filedir":  None, # used to be "sm_output". "" or None will give an error.
            "methodname":   "SmixDWS",
            "cmdheader":"%(cmdindex)03d", # Uh, only works once...
            "cmdindex":"%(cmdindex)03d",
            "source-rackname":"%(source-rackname)s",
            "destin-rackname":"tuberack1", # "%(destin-rackname)s", # -- No, this is not a choice at the moment.
            "source-row":"%(source-row)s",
            "source-col":"%(source-col)s",
            "destin-row":"%(destin-row)s",
            "destin-col":"%(destin-col)s",
            "transfer-vol-nl":"%(transfer-vol-nl)s",
            "cmd-comment":"%(cmd-comment)s",
            "sourcerack":"%(sourcerack)s",
            "slotnr":"%(slotnr)s",
            # Locations
            "dest-pos-names":"%(dest-pos-names)s"
            # NOT USED: If I'm implementing this functionality, I'll do it differently.
#            "placeit-24well-matdat":"./top/dws/trth/Rack_1_5ml_SAR", # Not used, AFAICS
#            "placeit-24well-matnam":"Rack_1_5ml_SAR",                # Not used, AFAICS
#            "placeit-staplerack-matdat":"./top/dws/plates/dwp96/AB_DWP_1200", # Not used, AFAICS
#            "placeit-staplerack-matnam":"AB_DWP_1200",              # Not used, AFAICS
        }
        # Attempt to move away from existing paradigm:
        self.ConstParams = {
            "filename": "sm-"+self.RunDateHourStr+".dws",
            "filedir":  None,
            "methodname":   "Staplemixer2",
            "destin-rackname":"tuberack1"
            , "usefiltertips":self.Usefiltertips
            # Additionally (set later): dest-pos-names,
        }
        self.Plateformats = {'24': dict(ncols=6, nrowmax=4),
                             '96': dict(ncols=12, nrowmax=8),
                             '384': dict(ncols=24, nrowmax=16)}
        #self.ConfigGenerator = ConfigGenerator()

        # OBS: Two types of configs! Can possibly  done smarter!
        #   1) Various configs, e.g. config[output] - incl what is in self.Configpars
        #   2) Robot configuration

        # Loading a complete config has not been tested yet. Thus, make sure the files does not exist
        # and use the default config from ConfigGenerator until you are ready to test it.

#            """ (which consists of first getting default config from ConfigGenerator,
#                 then mixing in self.Configpars, and finally trying to load a
#                 epmotion_staplemixer-robot.cfg file and mix that in.)
#            """
#            """ Notice:
#            Because it is so problematic to insert placeholders multiple times, (for cmdheader in particular),
#            you need to care about whether insertPlaceholders() is applied to the config or not.
#            If it is, then the config should be similar to that in ConfigGenerator.
#            If insertPlaceholders(cfg, self.Configpars) is not applied to the loaded config,
#            then the config needs to use %(cmdindex) rather than cmdheader and also define things such as labware, etc.
#            However, actually, for the initial round,
#            """
        """ Currently (14/3-13) I do the following:
            1) See if there is a global config to use. If not, get a config
            template from the ConfigGenerator class.
            2) Insert placeholders. This includes both dynamic (e.g. timestamps)
            as well as general placeholders (%(destin-rackname)s -> tuberack1, etc)
            (currently, the only applicable items are filename and destin-rackname)
            3) See if there is a designated robot.yml file. If there is,
                update config["robot"] with values from this.
            To be clear about the difference between the two configs:
                1) The global config will have placeholders replaced.
                2) The robot config will only have placeholders replaced once.
            In effect, this means that the cmdheader/cmdindex must be formatted
            differently in the global vs the robot config.
            The difference between global and robot-only config is that the
            global config can also be used to set:
                output filename and filedir and methodname (in dws file)
                modules (but these are currently specified by a .modulestopipet file)
            As such, there is really very limited use-case for the global config.
            I guess it was mostly a test to see whether it is smart so have a global
            config where parameters can be updated using a method like insertPlaceholders.
            But, it is not.
            EDIT:
                I now only try to load a robot config and not a global config.
                insertPlaceholders is pt always applied *one time* after load.
        """

        self.CmdTemplates = self.loadRobotCmdTemplate(robotcmdtemplatefile)

#            print "Failed to load epmotion_staplemixer-robot.yml config file, falling back to standard config template. "
#            # Get basic config "template".
#            self.CmdTemplates = self.ConfigGenerator.getCmdTemplates()
#            cfg = self.ConfigGenerator.getConfig() # I use a getter so I have the option to modify if I want...
#            self.Robotcmdtemplatefile = "< generated with ConfigGenerator! > (deprechated)"
##            yaml.dump(cfg,
#                      open('epmotion_staplemixer-config-before-placeholderinsertion.yml','wb'),
#                      default_flow_style=False, default_style='|')
            # Update basic config with dynamic values (timestamps in filename)
        #self.Config = self.insertPlaceholders(cfg, self.Configpars)
        # New paradigm. self.CmdTemplates is only updated once: just before
        # writing the cmd to file. Instead, self.ConstParams is updated as the
        # script initializes.

        #print "Printing the used config to file: epmotion_staplemixer-config-after-placeholderinsertion.yml"
#        yaml.dump(self.Config,
#                  open('epmotion_staplemixer-config-after-placeholderinsertion.yml','wb'),
#                  default_flow_style=False, default_style='|')

        self.read_rackfiles(rackfilenames)


    def loadRobotCmdTemplate(self, robotcmdtemplatefile):
        """
        Load yaml cmd template file.
         - robotcmdtemplatefile : filepath to yaml cmd template file.
        """
        try:
            cfg = yaml.load(open(robotcmdtemplatefile,'rU'))
            print("Using config/template file: {}".format(robotcmdtemplatefile))
            # config is NOT updated with Self.Configpars; I only update the config once, right before writing.
        except IOError as e:
            # No longer falling back!
            logger.error( "Failed to load robot cmd template file '%s', os.getcwd is: %s", robotcmdtemplatefile, os.getcwd() )
            raise e
        return cfg


    def insertPlaceholders(self, config, pars):
        """
        parse config (recursively for dict and lists) and modify strings with pars.
        """
        if isinstance(config, str):
            logger.debug("Interpolating config string '%s' with pars: %s", config, pars)
            config = config % pars
            logger.debug("Result is: %s", config)
        elif isinstance(config, dict):
            logger.debug("config is dict type")
            for item in config:
                config[item] = self.insertPlaceholders(config[item], pars)
        elif isinstance(config, (list, tuple)):
            logger.debug("config is list type")
            for i, item in enumerate(config):
                logger.debug("inserting for item %s", item)
                config[i] = self.insertPlaceholders(item, pars)
        else:
            print("insertPlaceholders: Unknown config.")
            print(config)
        logger.debug("Returning config: %s", config)
        return config


    def _read_rackfile(self, rackfilename):
        """
        Read rack data from file on disk.
        """
        with open(rackfilename, 'rU') as rackfile:
            # First do some sniffing...
            # Edit: I expect input smmc file to have headers!
            snif = csv.Sniffer()
            csvdialect = snif.sniff(rackfile.read(2048)) # The read _must_ encompass a full first line.
            #alternative:
#                sep =  max([',','\t',';'], key=lambda x: myline.count(x))
            csvdialect.lineterminator = '\n' # Ensure correct line terminator (\r\n is just silly...)
            rackfile.seek(0) # Reset file
            # Then, extract dataset:
            setreader = csv.DictReader(rackfile, dialect=csvdialect)
            # Import data
            # Note: Dataset is a list of dicts.
            rackdata = [row for row in setreader if row]
            #rackfileseqfield = fileutils.findFieldByHint(self.Rackdata[rackfilename][0].keys(), "seq")
            #for row in self.Rackdata[rackfilename]:
                # Create new or override... (moved to below)
        return rackdata



    def read_rackfiles(self, rackfilenames=None, forcerackfileseqfield=None):
        """
        Read data from rackfiles with paths provided in <rackfiles> argument.
        Stores the results in self.Rackdata.
        Returns self.Rackdata upon successful completion.
        """
        if rackfilenames is None:
            ext = ".rack.csv"
            #rackfilenames = [fname for fname in os.listdir(os.getcwd()) if fname[len(fname)-len(ext):] == ext] # filter
            rackfilenames = sorted(glob.glob("*"+ext))
            print("Autodetected rackfiles:" + str(rackfilenames))
        self.Racknames = [fileutils.removeFileExt(rackfilename, (".rack.csv", ".csv")) for rackfilename in rackfilenames]
        print("Racknames: {}".format(self.Racknames))
        if any(len(name)>21 for name in self.Racknames):
            print("WARNING! Some racknames might be longer than what is supported by EpMotion!")
            for longrackname in (name for name in self.Rackname if len(name)>21):
                print("Rack: %s (%s chars)" % (longrackname, len(longrackname)))
        self.Rackdata = OrderedDict() # keys are rackfilename

        for rackfilename in rackfilenames:
            self.Rackdata[rackfilename] = self._read_rackfile(rackfilename)

        #All rackdata is saved in self.RackData. Now, process this so it is easy to refer/lookup using a staple sequence.
        self.RackStaples = dict()
        # Note: "Modulename", "Sequence", etc is assumed. You may want to add functionality to grab alternative cases, but...
        # Also see new function compareDesignVsRackFiles where I add more functional rack_oligos data structure:
        for rackfilename, rackdata in list(self.Rackdata.items()):
            # The sequence field could be different in different rack datasets/files.
            # For each rack file, first find sequence field, and then make sure the sequence is properly written.
            if forcerackfileseqfield:
                rackfileseqfield = forcerackfileseqfield
            else:
                rackfileseqfield = fileutils.findFieldByHint(list(rackdata[0].keys()), "seq")
            #self.Rackseqfield = rackseqfield = "Sequence" # Override
            # Trim sequence (well, ensure you have a proper sequence in the "Sequence" field.
            for i, row in enumerate(rackdata):
                #logger.debug("rack: %s, row: %s, row.keys(): %s", rackfilename, i, row.keys())
                row["Sequence"] = row[rackfileseqfield].strip().replace(" ", "")
                row["rackname"] = fileutils.removeFileExt(rackfilename, (".rack.csv", ".csv")) # Nice to have...
                if len(row["Sequence"])<1:
                    logger.info("Notice: Empty sequence field in %s line %s", row["rackname"], i)
                else:
                    if row["Sequence"] in self.RackStaples:
                        print("""
WARNING! Staple sequence for row {row} in rackdataset
    {rackname}
already present in self.RackStaples.
This indicates redundancy, which is not gracefully supported.
Row:""".format(row=i, rackname=rackfilename))
                        print(row)
                    self.RackStaples[row["Sequence"]] = row

        return self.Rackdata


    def read_modulestopipetfile(self, modulestopipetfile=None):
        """
        Reads information from a file specifying which modules to pipet and how much to pipet
        for each module.
        NOTICE: StapleMixer.read_designfile() must have been invoked first, otherwise this will fail.
        CHANGES:
        - IT would really be simpler if you just have an OrderedDict[modulename]=volume, instead of
            having list[i] = {"Modulename":modulename, "ul":"5"}
        """
        # Define which modules to pipet.
        # modulestopipet is a simple reference list with modulename (string) and amount. Refer to self.DesignModules
        if modulestopipetfile is None:
            # If modulestopipetfile is not specified, use all modules from .smmc file with hard-coded volume...
            modulestopipet = [{"Modulename":modulename, "ul":"5"} for modulename in list(self.DesignModules.keys())]
        else:
            # I want to specify which oligos to pipet. But not implemented yet.
            # This file is also the place to specify how much to pipet. But that is also not implemented..
            # Should actually be a list of dicts with fields: Modulename, ul, <other?>
            if modulestopipetfile.lower() == "auto":
                # Use the first file named *.modulestopipet...
                modulestopipetfile = None
                for pat in ("*.modulestopipet", "*.modulestopipet.txt", "*pipetmodules*", "*module*pipet*"):
                    filelist =  glob.glob(pat)
                    if filelist:
                        modulestopipetfile = filelist[0]
            print("Using modulestopipet file: "+ modulestopipetfile)
            if modulestopipetfile is None:
                raise ValueError("No modulestopipet file found, aborting!")
            try:
                with open(modulestopipetfile,'rU') as pfh:
                    modulestopipet = [{"Modulename":fields[0], "ul":fields[1]}
                            for fields in [line.strip().split() for line in pfh] if len(fields)>0 and fields[0][0] != "#" ] # I used to split by '\t', but I now do like automapper and split by whitespace.
            except IOError as e:
                logger.error("Error '%s' while reading modulestopipetfile '%s', os.getcwd()='%s', sys.path=%s", e, modulestopipetfile, os.getcwd(), sys.path)
        print("modulestopipet:")
        #width = max(map(len, self.DesignModules.keys())) + 3
        width = max(len(x) for x in list(self.DesignModules.keys())) + 3
        print("\n".join(["{i[Modulename]:<{width}}{i[ul]} ul".format(i=item, width=width) for item in modulestopipet]))
        #                       self.Modulestopipet = modulestopipet
        return modulestopipet


    def read_designfile(self, designfilename):
        """
        Reads designfiles (e.g. the cadnano's .csv sequence exports).
        The result is stored as:
        - self.DesignDataset
        - self.DesignModules
        Returns (self.DesignDataset, self.DesignModules)
        """
        if designfilename is None:
            ext = ".smmc"
            dirlist = glob.glob("*"+ext)
            designfilename = dirlist[0]
            print("Designfilename: " + designfilename)
            if len(dirlist) > 1:
                print("Notice: There were multiple options for designfilename. (%s). I choose: %s" % (dirlist, designfilename))
        with open(designfilename, 'rU') as oligosetfile:
            # First do some sniffing (ps: you should only change dialect attributes if writing.)
            snif = csv.Sniffer()
            self.CsvDialect = snif.sniff(oligosetfile.read(4096))
            # Reset file and extract data as list of dicts:
            oligosetfile.seek(0)
            setreader = csv.DictReader(oligosetfile, dialect=self.CsvDialect)
            self.DesignFields = setreader.fieldnames # Save for a rainy day?
            self.DesignDataset = [row for row in setreader if len(row)>0]
        self.DesignSequenceFieldName = fileutils.findFieldByHint(list(self.DesignDataset[0].keys()), ("seq", "sequence"))
        self.DesignModuleFieldName = modulefield = fileutils.findFieldByHint(list(self.DesignDataset[0].keys()), ("Modulename", "moduleclass", "module", "class"))
        self.DesignModules = dict()
        # datastructure: self.DesignModules[<modulename>] = [list of row-dicts, one row per staple in the module]
        for row in self.DesignDataset:
            try:
                self.DesignModules.setdefault(row[modulefield], list()).append(row)
            except KeyError as e:
                print("KeyError %s while doing self.DesignModules.setdefault(row[modulefield], list()).append(row), row=%s, modulefield=%s" %(e, row, modulefield))
                raise e
        return (self.DesignDataset, self.DesignModules)

    def generateInstructionCsv(self, designfilename=None, modulestopipetfile="auto",
            pipdatafilenameformat="sm-{rundatetimestr}.pip.csv", reportname=None, plateconc=None):
        """
        # Reads design *.csv.smmc files and generates a *.cvs.pip instructions file with the following fields:
        # source-rackname, source-pos, destin-rackname, destin-pos, volume, comment.
        # comment is formatted like <module-name> : source-rackname:source-pos -> destin-rackname:destin-pos
        # If a "Modules-to-pipet.csv" is present, this can be used to specify which modules to pipet and how much to pipet of each module
        # Currently only support for one designfile, but this should be easily extendable...
        """
        if pipdatafilenameformat is None:
            pipdatafilenameformat = "sm-{rundatetimestr}.pip.csv"

        ## ----------- First, read design file and modulestopipet file ---------
        logger.debug("Reading design file: %s", designfilename)
        self.read_designfile(designfilename)
        logger.debug("Reading modulestopipet file: %s", modulestopipetfile)
        modulestopipet = self.read_modulestopipetfile(modulestopipetfile)

        # NB: Reading rack files has been refactored out in separate function, invoked upon epmotion_staplemixer object initialization.

        ## -------- Create pipet data ---------------#
        # Note: If you want to implement sorting and multi-key sorting (e.g. to pipet first by rack then by module), see
        # http://stackoverflow.com/questions/72899/in-python-how-do-i-sort-a-list-of-dictionaries-by-values-of-the-dictionary
        # http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys/1144405
        # source-rackname, source-pos, destin-rackname, destin-pos, volume, comment.
        pipetdataset = list()
        pipetrow = 0
        destrackname = "tuberack1"
        (ncorrect, nnotfound) = (0, 0)
        modulenames = [moduletopipet["Modulename"] for moduletopipet in modulestopipet]
        # initialize rackstats structure (dict of dicts)
        rackstats = { rackname : { modulename : 0 for modulename in modulenames } for rackname in self.Racknames }
        rackstats["not-found"] = { moduletopipet["Modulename"] : 0 for moduletopipet in modulestopipet }
        print("""
TODO: Mix staples in one rack first, then the next rack, then the next.
However, if oligos are sorted by modules in the order, this is probably not a big issue.
Also, the user might frequently prefer to pipet the modules in sequence,
finishing one module completely before starting on the next. That also
makes a fun more fail-safe, as it is easier to re-start the program after a failure.
""")
        logger.debug( "moduletopipet: %s", modulestopipet)
        for destindex, moduletopipet in enumerate(modulestopipet):
            volume = moduletopipet["ul"]
            modulename = moduletopipet["Modulename"]
            logger.debug("self.DesignModules[%s] : %s", modulename, self.DesignModules[modulename] )
            for modulerow in self.DesignModules[modulename]:
                pipetrow += 1
                logger.debug("self.RackStaples[%s]: %s", list(self.RackStaples.keys())[0], self.RackStaples[list(self.RackStaples.keys())[0]])
                try:
                    rackrow = self.RackStaples[modulerow[self.DesignSequenceFieldName]] # lookup the rackrow info using staple sequence.
                    # rackname stored as rackrow["rackname"]; other fields in the rackfile is stored as they appear in the *.rack.csv file.
                    sourcepos = rackrow[fileutils.findFieldByHint(list(rackrow.keys()), "pos")] # Can possibly be optimized by storing the field name for later ref.
                    pipetdataset.append(dict(list(zip(
                        self.PipDataFields, #["row","source-rackname","source-pos","destin-rackname","destin-index","volume","comment"]
                        [pipetrow, rackrow["rackname"], sourcepos, destrackname, str(destindex), str(volume),
                            "".join([modulename,": ", rackrow["rackname"],":",sourcepos,"->",destrackname,":",str(destindex)])
                        ]))))
                    rackstats[rackrow["rackname"]][modulename] += 1
                    ncorrect += 1
                    #comment is formatted like <module-name> : source-rackname:source-pos -> destin-rackname:destin-pos
                except KeyError as e:
                    print(" - \nKEY ERROR for module %s, oligo '%s' (keyed as %s) not found in rackdata. Modulerow: %s\n - " % \
                            (modulename, modulerow[self.DesignSequenceFieldName], e, modulerow))
                    nnotfound += 1
                    rackstats["not-found"][modulename] += 1
        self.PipetDataset = pipetdataset
        print("Staples found: " + str(ncorrect))
        print("Staples not found: " + str(nnotfound))

        ## ------ Write pipet data to file ----- ###
        pipdatafilename = pipdatafilenameformat.format(rundatetimestr=self.RunDateHourStr)
        logger.debug("self.PipDataFields and self.PipDataset created, writing to pipdatafilename: '%s' (os.getcwd()=%s)", pipdatafilename, os.getcwd())
        self.write_pipetdata_to_file(pipdatafilename) # Writes instructions to csv file.
        self.print_report(rackstats, plateconc, reportname, modulestopipet)
        return pipdatafilename



    def print_report(self, rackstats, plateconc, reportname, modulestopipet):
        """
        Printing rack-stats (to prompt and report file) is separated out to separate method.
        Also responsible for setting self.Configpars["dest-pos-names"].
        """

        modulenames = [moduletopipet["Modulename"] for moduletopipet in modulestopipet]
        modulenamewidth = max([ max(len(self.Modulenameprefix+x) for x in modulenames), len(r"Module \ Rack:") ])
        self.Racknamewidth = racknamewidth = max( len(x) for x in self.Racknames )
        logger.info( "Racknamewidth: {} ; modulenamewidth: {}".format(racknamewidth, modulenamewidth) )
        rackstatsstrhead = " | ".join(["{0:<{width}}".format(r"Module \ Rack:", width=modulenamewidth)]+self.Racknames+["not-found"] )
        rackstatsstr = "\n".join([ " | ".join(["{0:<{width}}".format(self.Modulenameprefix+modulename, width=modulenamewidth)]+\
            ["{count:^{width}}".format(count=rackstats[rackname][modulename], width=len(rackname))
                for rackname in self.Racknames+["not-found"] ] )
                for modulename in modulenames ])

        # Modules should be saved to destination rack ReagenzNamen. Modify self.ConstParams["dest-pos-names"]
        # Reagents names are saved as lines of the format:
        #       ReagenzName_0=RSPosition1
        #       StartVolumenNanoliter_0=111000
        #       ReagenzName_1=RSPosition2
        #       StartVolumenNanoliter_1=112000
        #       ReagenzName_23=RSPosition24
        #       StartVolumenNanoliter_23=124000

        destposnames = "\n".join(("ReagenzName_{index:0n}={modulename} ({nstaps:.0f})".format(
                                        index=i,
                                        modulename="".join((self.Modulenameprefix, module["Modulename"]))[-15:], # no reason, slices can go out of bounds.
                                        nstaps=len(self.DesignModules[module["Modulename"]]))
                                  for i, module in enumerate(modulestopipet) ))
        print("destposnames: (truncated to 20 char)")
        print(destposnames)
        #self.Configpars["dest-pos-names"] = destposnames
        self.ConstParams["dest-pos-names"] = destposnames

        # Make sure reportconc is defined, in case the user does ctrl+c escape.
        #reportconc = plateconc or self._getReportConcUserInput()
        # reportconc will be like: "25uM", "25", "", or None.
        if reportname is None:
            reportname = 'modules-report.txt'
        with open(reportname,'wb') as modulereport:
            modulereport.write("Robot cmd template/config file: {}\n\n".format(self.Robotcmdtemplatefile))
            modulereport.write("Modulename (uM /nstaps)\tModulename\tuM\tNstaps\tVol each\t\n")
            if plateconc:
                reportconcnum = plateconc # save this.
                # Test whether plateconc has a unit or is simply a number:
                try:
                    plateconc = int(float(plateconc))
                    # If user has only input a number, assume it is conc in uM:
                    concunit = "uM"
                except ValueError:
                    # User input non-numeric string, probably something like "25 uM". No need to add a unit manually.
                    concunit = ""
                modulespipetted = "\n".join(
                    "{modulename} ({conc}{concunit} /{nstaps})\t{modulename}\t{conc}\t{nstaps}\t{vol}\tul".format(
                            modulename=self.Modulenameprefix+module["Modulename"],
                            conc=reportconcnum, nstaps=len(self.DesignModules[module["Modulename"]]), vol=module["ul"], concunit=concunit)
                        for module in modulestopipet )
            else:
                # If user did not specify a concentration:
                modulespipetted = "\n".join( "".join([self.Modulenameprefix+module["Modulename"], " (", str(len(self.DesignModules[module["Modulename"]])), ")"])
                                    for module in modulestopipet )
            modulereport.write(modulespipetted)
            # Write a table with modules and how many oligos each module use from each plate
            modulereport.write("\n\nPlate usage statistics:\n")
            print(rackstatsstrhead)
            print(rackstatsstr)
            modulereport.write(rackstatsstrhead+'\n'+rackstatsstr)

        #self.Config["robot"]["method-prefix"]=self.insertPlaceholders(self.Config["robot"]["method-prefix"], self.Configpars)
        #print self.Config["robot"]["method-prefix"]
        # ----- END OF generateInstructionCsv() ----------


    def _getReportConcUserInput(self):
        """
        Obtains concentration via user input for the report.
        Refactored to separate method to enable monkeypatching during testing.
        """
        reportconc = None
        try:
            reportconc = input("Specify source concentration (for report; optional): ")
        except KeyboardInterrupt:
            pass
        return reportconc


    def write_pipetdata_to_file(self, pipdatafilename):
        """
        Does the actual writing of creating a csv file with pipetting instructions.
        Not really required, but may be useful in some cases.
        """
        logger.debug("Writing pipdata to pipdatafile: %s", pipdatafilename)
        with open(pipdatafilename, 'wb') as pipdatafile:
            dw = csv.DictWriter(pipdatafile, self.PipDataFields)
            # Python specific:
            if hasattr(dw, 'writeheader'):
                dw.writeheader() # Requires python 2.7+
            else:
                dw.write(self.CsvDialect.delimiter.join(self.FileFields) + "\n") # Just as quick...
            dw.writerows(self.PipetDataset)
        print("Pipetdata written to file: "+ pipdatafilename)


    def getPipetdataFromFiles(self, pipetfiles, onefileonly):
        """
        Refactored from generateRobotFile(),

        """
        if pipetfiles is None:
            ext = ".pip.csv"
            dirlist = [fname for fname in os.listdir(os.getcwd()) if fname[len(fname)-len(ext):] == ext] # filter
            dirlist = glob.glob("*"+ext)
            if onefileonly:
                pipetfiles = (dirlist[:len(dirlist)-1], )
            else:
                pipetfiles = dirlist
        pipetdataset = list()
        for pipetfilename in pipetfiles:
            with open(pipetfilename, 'rU') as pfile:
    #                snif = csv.Sniffer()
    #                dialect = snif.sniff(pfile.read(1024))
    #                pfile.seek(0) # Reset file
                setreader = csv.DictReader(pfile)
                filedata = [row for row in setreader if len(row)>0]
            pipetdataset += filedata # All rows should just be one long dataset.
        return pipetdataset


    def generateRobotFile(self, fromfiles=True, pipetfiles=None, onefileonly=True,
        dwsfilenamestrfmt=None, aux_resuspend=False):
        """
        # fromfiles: if set to false, this method will try to use self.PipetDataset.
        # pipetfiles: read from these files. If not specified, the method will search for files ending with ".pip.csv".
        # @onefileonly: Only read one pipetdataset .pip.csv file even if multiple files are found.
        # @dwsfilenamestrfmt: Not implemented; it is tedious, because the filename is also given in self.Configpars and self.ConstParams.
        Requires the following attributes to be generated:
            self.PipetDataset (or pipetdata from files), both normally generated by self.generateInstructionCsv
            self.CmdTemplates, generated by self.loadRobotCmdTemplate during __init__()
        Note:
            as stated in the following discussion: http://bugs.python.org/issue1286
            it is not good practice to have a long with statement half-way down your method.
            Either:
                Receive an open filehandle as argument to the method, e.g.:
                def method_a(self, ...)
                    do some basic initial stuff, keeping the file SHORT
                    with open(filepath) as fh:
                        self.process(fh)
                def process(self, fh):
                    <do some processing with fh>
            Or:
                def method_a(self, ...)
                    <produce a data struct>
                    self.saveFile(data)
                def saveFile(self, data):
                    with open(filepath, 'wb') as fh:
                        fh.write(data)

        """

        ## --- FIRST, get pipet data (csv or reuse) ------- ##
        if fromfiles:
            pipetdataset = self.getPipetdataFromFiles(pipetfiles, onefileonly)
        else: #fromfile is False
            pipetdataset = self.PipetDataset

        # Run though the data and figure out the source-racknames that are actually used/required.
        sourceracks = set([row["source-rackname"] for row in pipetdataset])
        sourceracks = fileutils.natural_sort(sourceracks) # List and sort, using natural sort.


        ## ---- SECOND, write pipet data to file: ------- #
        robotcmdfilename = self.Configpars["filename"] #"sm-"+self.RunDateHourStr+".dws"
        if "filedir" in self.Configpars and self.Configpars["filedir"]:
            outputdir = self.Configpars["filedir"]
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
        else:
            outputdir = os.getcwd()
        filepath = os.path.join(outputdir, robotcmdfilename)
        cmdnum = 1
        robotvalet = EpmotionValet() # In theory, this would make it easier to use other robots...


        # Changed: I now write to a StringIO object rather than directly to a file, and
        # then ship the StringIO object to a dedicated file_writing class.
        #with open(filepath, 'wb') as robotfile:
        #with StringIO.StringIO() as robotfile:
        # 'with' statement not supported for StringIO in python2.7 (only 3.3+), c.f. http://bugs.python.org/issue1286
        # Eliminating the "with" wrapper:
        robotfile = io.StringIO()
        # Initial, constant cmds:
        #robotfile.write(self.Config["robot"]["method-prefix"])
        pars = self.ConstParams.copy() # Shallow copy only; I do not think deep is required.
        #print "pars:"
        # Method-prefix: currently also includes the place-it command for the destination rack.
        robotfile.write(self.CmdTemplates["method-prefix"] % self.ConstParams)
        cmdnum += 1 # "method-prefix contains [001] (Place-it, 1.5 ml tube rack)
        robotvalet.Slots[160] = True # dest-rack occupies this.
        # Place It Cmds:
        # Add a tub, if resuspend-then-transfer feature is activated (implementation in progress)
        if aux_resuspend:
            ## NOTICE: BufferTub cannot be in pos C4 or row A. Pos B3 is thus preferred.
            pars = dict(self.ConstParams, cmdindex=cmdnum)
            template = self.CmdTemplates["cmd-placeit-tub"]
            # edit: robotvalet does use slot 159, but Tub cannot be there either.
            # On the other hand, I have been getting errors if I just place the tub n B3 directly (these errors was due to a missing pre-run cmd.)
            # Use slot nr 154 = B3
            if robotvalet.Slots[154] == True:
                raise NotImplementedError("Robot valet Slots[159] is already occupied. Accounting for this case is not yet implemented")
            else:
                robotvalet.Slots[154] = True # Occupy it.
            robotfile.write(template % pars)
            cmdnum += 1
        # a) Place racks with staples:
        for sourcerack in sourceracks:
            slotnr = robotvalet.valet("sourcerack")
            if slotnr is None:
                print("ERROR! Slot no is None! (sourcerack " + sourcerack + ")")
            #robotfile.write(self.Config["robot"]["cmd-placeit-rack"] % {"cmdindex":cmdnum, "slotnr":slotnr, "sourcerack":sourcerack})
            #print "self.ConstParams:"
            #print self.ConstParams
            pars = self.ConstParams.copy()
            # Note: for some weird reason you cannot do copy().update(...) in a single operation?
            pars.update({"cmdindex":cmdnum, "slotnr":str(slotnr), "sourcerack":sourcerack})
            #print 'pars: and self.CmdTemplates["cmd-placeit-rack"]'
            #print pars
            #print self.CmdTemplates["cmd-placeit-rack"]
            robotfile.write(self.CmdTemplates["cmd-placeit-rack"] % pars)
            cmdnum += 1
        # b) Place tips: (just enough to pipet all staples)
        for ntipracks in range(len(pipetdataset)/96+1):
            # Fill with tips, but no more than needed.
            slotnr = robotvalet.valet("tips")
            if slotnr is None:
                # This can happen if we have more sampletransfers than there is room for tips, and is not a big deal.
                print("Notice: Slot nr is None! (ntiprack" + str(ntipracks) + ")")
                continue
#                robotfile.write(self.Config["robot"]["cmd-placeit-tips"] % {"cmdindex":cmdnum, "slotnr":slotnr})
            #pars = self.ConstParams.copy()
            #pars.update({"cmdindex":cmdnum, "slotnr":slotnr})
            pars = dict(self.ConstParams, cmdindex=cmdnum, slotnr=slotnr, tiptype="tip50f")
            robotfile.write(self.CmdTemplates["cmd-placeit-tips"] % pars)
            cmdnum += 1

        # Commands after placeit, but before sample transfers:
        for template in self.CmdTemplates["cmds-after-placeit"]:#Config["robot"]["cmds-after-placeit"]:
            #print "cmds-after-placeit instruction: "
            #print instruction
            # cmds-after-placeit are not exchanged during robot writing.
            # at this point I still have %(cmdheader)s and not %(cmdindex)03d
            # Thus, I need for first convert %(cmdheader)s to %(cmdindex)03d and then insert.
            # Notice, trick: First replace header with format spec for index, then insert index value.
#                robotfile.write(template % dict(cmdheader="%(cmdindex)03d") % {"cmdindex":cmdnum})
            #pars = self.ConstParams.copy()
            #pars.update({"cmdindex":cmdnum})
            # Ah, http://pommereau.blogspot.dk/2009/05/copy-python-dict-with-updates.html
            # first doing a copy, then an update is equivalent of:
            # newdict = dict(olddict, newentry1=val1, newentry2=val2, etc.)
            # or alternatively: newdict = dict(olddict1, **olddict2)
            pars = dict(self.ConstParams, cmdindex=cmdnum, cmdheader=cmdnum) # use of cmdheader is only temporary!
            robotfile.write(template % pars)
            cmdnum += 1
        # SampleTransfer cmds from pipetdataset (*.pip.csv file)
        tub_no = 1
        tub_vol_used = 0
        for instruction in pipetdataset:
            # Add a tub, if resuspend-then-transfer feature is activated (implementation in progress)
            instruction = self.pipetinstructionToCmdVars(instruction)
            #instruction["cmdindex"] = cmdnum
            if aux_resuspend:
                # Add tub (remember to reserve slot with robot workplace valet)
                """ Regarding adding a 'resuspend' step before hand:
                    1) The purpose of doing this is soly to save tips and a bit of time.
                    2) It only makes sense if using the same tool, typically the T300 which requires
                        a minimum volume of 20 ul. So, if you only want to sample 10 ul after redissolving,
                        that must be performed in a separate step.
                    3) If doing this, use the following change-tip settings:
                        > For tub->DWP: Don't/never change tip.
                        > For DWP->Tube: Change tip when command finishes.
                """
                pars = dict(self.ConstParams, cmdindex=cmdnum, **instruction)
                resuspendvol = pars["resuspend-vol"] = int(round(self.ResuspendPlateVol[instruction["source-rackname"]][instruction["source-pos"]]*1000)) # times 1000 to nanoliter
                tub_vol_used += resuspendvol/1000
                #print "tub_vol_used: {}".format(tub_vol_used)
                pars["resuspend-mix-vol"] = resuspendvol-23*1000
                pars["tub_no"] = tub_no
                if tub_vol_used > 25000:
                    tub_no += 1
                    print("BufferTub tub_no increased to {}".format(tub_no))
                    tub_vol_used = 0
                    if tub_no > 3:
                        raise NotImplementedError("Method not implemented for volumes larger than 3 x 25 ml!")
                template = self.CmdTemplates["cmd-redissolve-before-template"]
                robotfile.write(template % pars)
                cmdnum += 1
                #instruction["cmdindex"] = cmdnum

            instruction = self.pipetinstructionToCmdVars(instruction)
            #instruction["cmdindex"] = cmdnum
            #instruction["cmdheader"] = cmdnum # This is only temporary
#                robotfile.write(self.Config["robot"]["cmd-template"] % instruction)
            #pars = self.ConstParams.copy().update(instruction)
            pars = dict(self.ConstParams, cmdindex=cmdnum, **instruction) # better way of copy+update
            robotfile.write(self.CmdTemplates["cmd-template"] % pars)
            cmdnum += 1
            ## TODO: "cmd-template" should be renamed to "sampletransfer".
        # Finishing cmds:
        for template in self.CmdTemplates["method-postcmds"]:#self.Config["robot"]["method-postcmds"]:
            #pars = self.ConstParams.copy().update({"cmdheader":cmdnum, "cmdindex":cmdnum})
            pars = dict(self.ConstParams, **{"cmdheader":cmdnum, "cmdindex":cmdnum})
            robotfile.write(template % pars)
            cmdnum += 1
        # Write the StringIO object to filesystem:
        self._writeStringIOtoFile(robotfile, filepath)

        print("Robot method/program/application written to file: " + filepath) # robotcmdfilename
        print(" -- total instructions: " + str(cmdnum))
        print(" -- sample transfers: " + str(len(pipetdataset)))

        return filepath
    # end def generateRobotFile()

    def _writeStringIOtoFile(self, robotfile, filepath):
        logger.debug("Writing robotfile StringIO %s to file: '%s'", robotfile, filepath)
        with open(filepath, 'wb') as fh:
            fh.write(robotfile.getvalue())
        return True


    def generateResuspendDws(self, resuspendconc, sortby='volume',
                             transferAliquotToDestRack=False, transferDestStartIndex=0, tranferAliquotVolume=None,
                             destformat='96'):
        """
        Will make a dws method for resuspending oligos in a plate but not mix these into modules.
        Requires the following attributes to be generated:
            self.ResuspendPlateVol (or pipetdata from files), generated by self.gen_resuspend_plate_vol()
            -   self.Rackdata, used by self.gen_resuspend_plate_vol,
                is generated by self.read_rackfiles() during __init__()
            self.CmdTemplates, generated by self.loadRobotCmdTemplate during __init__()
        # Note: the rack file should include positions for each entry.
        # This means that there is no reason to specify plate format for the source rack!
        Arguments:
        - transferAliquotToDestRack: Transfer an aliquot from the well after resuspending.
        - transferDestStartIndex: If transferAliquotToDestRack is True, this will specify which position in the dest rack to start from.
        - tranferAliquotVolume: How much to transfer. If boolean false, will transfer all minus 25 ul.
        """

        logger.info( "resuspendconc is %s", resuspendconc )
        logger.info( "sortby is %s", sortby )
        logger.info( "transferAliquotToDestRack is %s", transferAliquotToDestRack )
        logger.info( "transferDestStartIndex is %s", transferDestStartIndex )
        logger.info( "tranferAliquotVolume is %s", tranferAliquotVolume )
        logger.info( "destformat is %s", destformat )

        # FIRST, adjust self.Configpars and calculate the concentrations for each well:
        self.Configpars['destin-rackname'] = 'destination-plate'
        if isinstance(destformat, str):
            destformat = self.Plateformats[destformat]

        self.gen_resuspend_plate_vol(target_conc = resuspendconc, raiseErrorAbove=None)
        # info is saved in self.ResuspendPlateVol[rackname][pos]

        ## ---- Information on file path and other inits... ------- #
        robotcmdfilename = self.Configpars["filename"] #"sm-"+self.RunDateHourStr+".dws"
        if "filedir" in self.Configpars and self.Configpars["filedir"]:
            outputdir = self.Configpars["filedir"]
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
        else:
            outputdir = os.getcwd()
        filepath = os.path.join(outputdir, robotcmdfilename)
        cmdnum = 1
        robotvalet = EpmotionValet() # In theory, this would make it easier to use other robots...


        #################################
        # Writing part to DWS:
        #################################
        #with open(filepath, 'wb') as robotfile:
        robotfile = io.StringIO()
        # -------------------------------------
        # Write first, constant part of DWS:
        #--------------------------------------
        pars = dict(self.ConstParams, **{"dest-pos-names":""}) # Easier way to make a shallow copy and update it on the same line.
        # The method-precix cmd template currently also includes a place-it command for the destin-rackname (i.e. 'tuberack1')
        robotfile.write(self.CmdTemplates["method-prefix"] % pars)
        cmdnum += 1 # "method-prefix contains [001] (Place-it, 1.5 ml tube rack)
        robotvalet.Slots[160] = True # dest-rack occupies this.
        # Place It Cmds:
        # Add a tub for buffer:
        ## Notice: BufferTub cannot be in pos C4 or row A. Pos B3 is thus preferred.
        pars = dict(self.ConstParams, cmdindex=cmdnum)
        try:
            template = self.CmdTemplates["cmd-placeit-tub"]
        except KeyError as e:
            logger.error("Could not find command template 'cmd-placeit-tub' in CmdTemplates. \
                         Perhaps your epmotion-cmd-templates.yml does not contain this?\
                         self.CmdTemplate.keys() is: %s\
                         and os.getcwd() is: %s", list(self.CmdTemplates.keys()), os.getcwd())
            raise e
        # edit: robotvalet does use slot 159, but Tub cannot be there either.
        # On the other hand, I have been getting errors if I just place the tub n B3 directly (these errors was due to a missing pre-run cmd.)
        # Use slot nr 154 = B3
        if robotvalet.Slots[154] == True:
            raise NotImplementedError("Robot valet Slots[159] is already occupied. Accounting for this case is not yet implemented")
        else:
            robotvalet.Slots[154] = True # Occupy it.
        robotfile.write(template % pars)
        cmdnum += 1

        # a) Place racks with staples:
        for sourcerack in self.Racknames:
            slotnr = robotvalet.valet("sourcerack")
            if slotnr is None:
                print("ERROR! Slot no is None! (sourcerack " + sourcerack + ")")
            pars = dict(self.ConstParams, **{"cmdindex":cmdnum, "slotnr":str(slotnr), "sourcerack":sourcerack})
            robotfile.write(self.CmdTemplates["cmd-placeit-rack"] % pars)
            cmdnum += 1
        # b) Place tips: (just enough to pipet all staples)
        ntipsneeded = dict(tip50f=0, tip300f=0, tip1000f=0, tip50=0, tip300=0, tip1000=0)
        def tiptypefromvolume(vol):
            return "tip{}{}".format(50 if vol <= 50 else 300 if vol <= 300 else 1000, "f" if self.Usefiltertips else "")
        for rackname, rackentries in list(self.ResuspendPlateVol.items()):
            for pos, vol in list(rackentries.items()):
                ntipsneeded[tiptypefromvolume(vol)] += 1
        logger.info( "ntipsneeded: %s", ntipsneeded )
        # Fill with tips, but no more than needed.
        for tipsize, tipsizecount in list(ntipsneeded.items()):
            for ntipracks in range((tipsizecount-1)/96+1): # python2 is doing floor division; change for python3.
                slotnr = robotvalet.valet("tips")
                if slotnr is None:
                    # This can happen if we have more sampletransfers than there is room for tips, and is not a big deal.
                    print("Notice: Slot nr is None! (ntiprack" + str(ntipracks) + ")")
                    continue
                pars = dict(self.ConstParams, cmdindex=cmdnum, slotnr=slotnr, tiptype=tipsize)
                robotfile.write(self.CmdTemplates["cmd-placeit-tips"] % pars)
                cmdnum += 1

        # Commands after placeit, but before sample transfers:
        for template in self.CmdTemplates["cmds-after-placeit"]:#Config["robot"]["cmds-after-placeit"]:
            pars = dict(self.ConstParams, cmdindex=cmdnum, cmdheader=cmdnum) # use of cmdheader is only temporary!
            robotfile.write(template % pars)
            cmdnum += 1

        ###############################################
        ## Write a cmd for each well in each rack:   ##
        ###############################################
        tub_no = 1
        tub_vol_used = 0
        vol_resuspend_count = 0
        aliquot_transfer_count = 0
        aliquot_transfer_volsum = 0
        destin_index = transferDestStartIndex
        logger.debug("Creating sampletransfer cmds, sorted by %s, i.e. itemgetter(%s)", sortby, 1 if sortby=='volume' else 0)
        for rackname, rackentries in list(self.ResuspendPlateVol.items()):
            # self.ResuspendPlateVol[rackname][pos]
            # rackentries[pos]=resuspendvol
            # Re: sorting a dict: http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
            # rackentries.items() returns a sequence of two-item tuples.(key,value)
            # after key=operator.itemgetter(1), invoking key(kvtuple) will yield kvtuple[1]
            for pos, vol in sorted(list(rackentries.items()), key=operator.itemgetter(1 if sortby=='volume' else 0), reverse=True if sortby=='volume' else False):
                vardict = {"cmdheader":cmdnum, "cmdindex":cmdnum}
                pars = dict(self.ConstParams, **vardict)
                # standard parsvars include: cmdindex,
                # special pars for cmd-redissolve-before-template include: tub_no, source-rackname,
                # PAY ATTENTION: source-* values refer to the rack with the staples; not the buffer tub.
                # I usually just throw the pipet instructions to instruction = self.pipetinstructionToCmdVars(instruction),
                # which converts A01-like pos to destin-row,destin-col values and volume to volume-transfer-nl.
                # But, I might as well do this my self also.
                pars['source-rackname'] = rackname
                # Note: the rack file should include positions for each entry.
                # This means that there is no reason to specify plate format for the source rack!
                pars['source-row'], pars['source-col'] = posToRowColTup(pos)
                pars['tool'] = "TS_50" if vol <= 50 else "TS_300" if vol <= 300 else "TS_1000"
                pars["resuspend-vol"] = resuspendvol = int(round(vol*1000)) # times 1000 to nanoliter
                tub_vol_used += vol # this is in ul...
                pars["resuspend-mix-vol"] = resuspendvol-40*1000  # Use all but 40 ul to mix with.
                pars["tub_no"] = tub_no  # the tub to aspiarate from
                pars["cmd-comment"] = "{}:{} (rack:pos) resuspending with {} ul.".format(rackname, pos, vol)
                if tub_vol_used > 25000:
                    tub_no += 1
                    print("BufferTub tub_no increased to {}".format(tub_no))
                    tub_vol_used = 0
                    if tub_no > 3:
                        raise NotImplementedError("Method not implemented for volumes larger than 3 x 25 ml!")

                template = self.CmdTemplates["cmd-redissolve-before-template"]
                if transferAliquotToDestRack:
                    # EnumEjectTips: 1="When command finishes", 2="Change tips before each aspiration, well",
                    #   3="Change tips before each aspiration", 4="Do not change tips"
                    template = template.replace("EnumEjectTips=1", "EnumEjectTips=4") # Make sure the robot does not change tip if you want to transfer an aliquot.
                robotfile.write(template % pars)
                cmdnum += 1
                vol_resuspend_count += 1
                ## If you want, this is the place to add a transfer logic that transfers some or all the resuspended volume to a new plate:
                if transferAliquotToDestRack:
                    template = self.CmdTemplates["cmd-aliquot-transfer-after-resuspend-template"]
                    # can reuse the following params: source-rackname, source-row, source-col,
                    # possibly, but recalculate: tool
                    destpos = indexToPos(destin_index, **destformat)
                    pars["cmd-comment"] = "Aliquotting from {}:{} {} ul to {}:{}".format(rackname, pos, vol, pars['destin-rackname'], destpos)
                    pars['destin-row'], pars['destin-col'] = indexToRowColTup(destin_index, **destformat)
                    destin_index += 1
                    aliquot_transfer_vol = tranferAliquotVolume or (vol-25)
                    logger.debug( "aliquot_transfer_vol is %s", aliquot_transfer_vol*1000 )
                    pars['transfer-vol-nl'] = aliquot_transfer_vol*1000
                    pars['tool'] = "TS_50" if aliquot_transfer_vol <= 50 else "TS_300" if aliquot_transfer_vol <= 300 else "TS_1000"
                    pars["cmdindex"] = cmdnum
                    robotfile.write(template % pars)
                    cmdnum += 1
                    aliquot_transfer_count += 1
                    aliquot_transfer_volsum += aliquot_transfer_vol





        ###########################################
        ## Write last, constant part of DWS file ##
        ###########################################
        # Finishing cmds:
        for template in self.CmdTemplates["method-postcmds"]:#self.Config["robot"]["method-postcmds"]:
            #pars = self.ConstParams.copy().update({"cmdheader":cmdnum, "cmdindex":cmdnum})
            pars = dict(self.ConstParams, **{"cmdheader":cmdnum, "cmdindex":cmdnum})
            robotfile.write(template % pars)
            cmdnum += 1

        # Done with the robot file; with statement handles closing.
        # Edit: throwing robotfile StringIO to _writeStringIOtoFile
        self._writeStringIOtoFile(robotfile, filepath)

        print("Robot method/program/application written to file: " + filepath) # robotcmdfilename
        print(" -- total instructions: {}".format(cmdnum))
        print(" -- number of resuspensions: {}".format(vol_resuspend_count))
        print(" -- total resuspend vol: {}".format( sum( sum(rackentries.values()) for rackentries in list(self.ResuspendPlateVol.values()) ) ))
        print(" -- minimum resuspend vol: {}".format( min( min(rackentries.values()) for rackentries in list(self.ResuspendPlateVol.values()) ) ))
        print(" -- maximum resuspend vol: {}".format( max( max(rackentries.values()) for rackentries in list(self.ResuspendPlateVol.values()) ) ))
        print(" -- instructions sotred by: rack, then {}".format(sortby))
        print(" -- number of aliquot transfers: {}".format(aliquot_transfer_count))
        print(" -- total aliquot transfers vol: {}".format( aliquot_transfer_volsum ))

        return filepath

    # end def generateResuspendDws




    def pipetinstructionToCmdVars(self, instruction):
        """ Creates destin-row etc named arguments from pipet instruction
        (line in *.pip.csv file)
        This can (in theory) be implemented as a per-robot basis...
        """
        # Make sure source-pos is converted to source-row and source-col.
        if not ("source-row" in list(instruction.keys())) and not ("source-col" in list(instruction.keys())):
            (instruction["source-row"], instruction["source-col"]) = posToRowColTup(instruction["source-pos"])
        # Same for destin-pos
        if not ("destin-row" in list(instruction.keys())) and not ("destin-col" in list(instruction.keys())):
            if "destin-pos" in list(instruction.keys()):
                (instruction["destin-row"], instruction["destin-col"]) = posToRowColTup(instruction["destin-pos"])
            else:
                # Remember that destination is in a 4 by 6 tube rack.
                (instruction["destin-row"], instruction["destin-col"]) \
                   = indexToRowColTup(instruction["destin-index"], ncols=6, nrowmax=4)
        if not "transfer-vol-nl" in instruction:
            # Should be int, not float. But, instruction["volume"] might be float,\
            # and in theory so could 1000*instruction["volume"]. Int typecasting does not round properly.
            instruction["transfer-vol-nl"] = "{:.0f}".format(float(instruction["volume"])*1000)

        return instruction



    def gen_resuspend_plate_vol(self, target_conc=160, raiseErrorAbove=None):
        """
        Populates self.ResuspendPlateVol as data structure:
            ResuspendPlateVol[<rackname>][<pos>] = volume
        where [<rackname>][<pos>] identifies a well in a particular rack plate,
        and volume is the volume to resuspend to in order to obtain target_conc.
        """
        if raiseErrorAbove is None:
            raiseErrorAbove = self.Resuspend_maxvol
        self.ResuspendPlateVol = OrderedDict() # dict[plate][pos] = vol
        # self.Rackdata[rackfilename] = [list of rows in rackfile] - no, wait; I used DictReader, so it is a list of dicts :)
        # use Rackdata[rackfilename][idx]["rackname"] for rackname without file extension.
        for rackdata in list(self.Rackdata.values()):
#            print "rackfilename: {}\nrowdict: {}".format(rackfilename,rowdict)
            try:
                for rowdict in rackdata:
                    vol = float(rowdict["nmoles"])*1000/target_conc
                    if raiseErrorAbove and vol > raiseErrorAbove:
                        raise ValueError("gen_resuspend_plate_vol: volume too large ({} ul".format(vol))
                    rowdict["final_vol_ul"] = self.ResuspendPlateVol.setdefault(rowdict["rackname"], dict())[rowdict["Pos"]] = vol
            except KeyError:
                logger.error("KeyError, rowdict.keys=%s, rowdict=%s", list(rowdict.keys()), rowdict)
        logger.debug("Calculated field 'final_vol_ul' for all rows in self.Rackdata. This is also available specifically in self.ResuspendPlateVol.")





if __name__ == "__main__":


    import argparse
    parser = argparse.ArgumentParser(description="""
    Staplemixer: Takes a list of staples, e.g. a *.smmc file created with automapper,
    together with one or more plate files (*.rack.csv) and a modulestopipet file,
    and produce from these a *.dws file that will programme the epmotion robot.""")
    parser.add_argument('-f', '--designfilename', help="The exported cadnano sequence list, comma-separated file (*.csv).")
    parser.add_argument('-m', '--modulestopipetfile', help="File specifying which modules to pipet and how much to pipet, \
                        with the two values are separated by whitespace.")
    parser.add_argument('-o', '--outputfilenamefmt', help="How to format the filename of the robot output file (*.dws)")
    parser.add_argument('--plateconc', metavar='<conc_in_uM>', type=int, help="Specify the concentration of the plates. \
                        Used as information in the report file.")
    parser.add_argument('--reportname', help="The filename of the pipetting report file that documents what \
                        has been pipetted when this program is completed.")

    parser.add_argument('--nofiltertips', action='store_true', help="Do not use filter-tips. \
                        Default is false (= do use filter tips)")
    parser.add_argument('-r', '--rackfiles', nargs='*', help="Specify which rackfiles to use. \
                        If not specified, all files ending with *.rack.csv will be used. This arguments will \
                        take all following arguments, and can thus be used as epmotion_staplemixer -r *.racks")


    parser.add_argument('--init_resuspend', metavar='<conc_in_uM>', type=int, help="Perform an initial resuspension of \
                        the staple strands to the specified concentration before pipetting. Conc is assumed to \
                        be in uM, \and the rackfiles must have an 'nmoles' field in the header.")
    parser.add_argument('--resuspend_only', metavar='<conc_in_uM>', type=int, help="Resuspend oligos to the \
                        specified concentration. Uses all found rack.csv files as rackfiles. \
                        If this is used, all arguments for module/design pipetting are ignored.")
    parser.add_argument('--resuspend_maxvol', metavar='<maximum plate volume>', type=int,
                        help="Specifies the maximum volume available in the well plates. \
                             If the specified concentration requires a higher volume, a ValueError is raised.")
    parser.add_argument('--resuspend_sortby', choices=('volume', 'pos'), default='volume',
                        help="Specify the plate format. Valid arguments are: 24, 96, 384.")

    parser.add_argument('--destformat', choices=('24', '96', '384'), default='96',
                        help="Specify the destination plate format. Valid arguments are: 24, 96, 384.")

    parser.add_argument('--resuspend_transferaliquot', action='store_true',
                        help="After resuspending, transfer an aliquot to the destination rack. *ONLY* compatible with --resuspend_only, not --init_resuspend.")
    parser.add_argument('--resuspend_aliqouot_deststartindex', metavar='<start index>', type=int, default=0,
                        help="The starting index for the destination rack for aliquot transfers after resuspending.")
    parser.add_argument('--resuspend_aliqouot_volume', metavar='<start index>', type=int, default=None,
                        help="The the aliquot volume to transfer to dest rack after resuspending. Defaults to use the complete volume minus 25 ul.")

    parser.add_argument('--resuspend_plate_format', help="Specify the plate format for the rack(s) that are to be resuspended. Valid arguments are: 24, 96, 384.")
    parser.add_argument('--modulenameprefix', default='', help="Prefix all modulenames with this (e.g. the design group name).")

    parser.add_argument('--debug', metavar='<MODULES>', nargs='*',
                        help="Enable debug logging. If nothing is specified, will enable debug logging for all modules.")

    argsns = parser.parse_args() # produces a namespace, not a dict.
    # But you cant just toss a random dict into functions or methods anyways, will produce a
    # TypeError: func() got an unexpected keyword argument


    logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s"
    if argsns.debug is None:
        #and 'all' in argsns.debug:
        logging.basicConfig(level=logging.INFO, format=logfmt)
        logger.debug("Log-level set to INFO.")
    # argsns.debug is a list (possibly empty)
    elif argsns.debug:
    # argsns.debug is a non-empty list
        logging.basicConfig(level=logging.INFO, format=logfmt)
        for mod in argsns.debug:
            logger.info("Enabling logging debug messages for module: %s", mod)
            logging.getLogger(mod).setLevel(logging.DEBUG)
    else:
        # argsns.debug is an empty list, debug ALL modules:
        logging.basicConfig(level=logging.DEBUG, format=logfmt)
        logger.debug("Log-level set to DEBUG.")


    usefiltertips = not argsns.nofiltertips

    sm = StapleMixer(rackfilenames=argsns.rackfiles, usefiltertips=usefiltertips, modulenameprefix=argsns.modulenameprefix)
    if argsns.resuspend_maxvol:
        sm.Resuspend_maxvol = argsns.resuspend_maxvol
    # could be made more elegant, e.g. using a single "outputfilenamefmt" formatted as "sm-{runtime}-uservals-{ext}"
    if argsns.outputfilenamefmt:
        sm.Configpars["filename"] = sm.ConstParams["filename"] = argsns.outputfilenamefmt+".dws"
        pipdatafilenameformat = argsns.outputfilenamefmt+".pip.csv"
    else:
        pipdatafilenameformat = None
    if argsns.init_resuspend:
        # init_resuspend is used to first re-dissolve oligos and then perform standard pipetting.
        try:
            logger.debug("Calculating field 'final_vol_ul' for all rows in sm.Rackdata. This is also available specifically in sm.ResuspendPlateVol.")
            print("Adding redissolve steps to {} uM.".format(argsns.init_resuspend))
            sm.gen_resuspend_plate_vol(int(argsns.init_resuspend))
        except TypeError as e:
            print("init_resuspend: ERROR. You must now provide the target concentration in uM after the parameter")
            print(e)
    if argsns.resuspend_only:
        # resuspend_only is used if you want to make a robot method that *only* does resuspension to a
        # specific concentration (calculating volume) and nothing else.
        # Note: the rack file should include positions for each entry.
        # This means that there is no reason to specify plate format for the source rack!
        # Other note: Currently not catching e.g. TypeErrors. If it fails, I want the whole script to fail.
        print("Adding redissolve steps to {} uM.".format(argsns.resuspend_only))
        print("Will redissolve racks by rack then volume, but not perform any pipetting.")
        #sm.gen_resuspend_plate_vol(int(argsns.resuspend_only)) # is handles by the generateResuspendDws method.

        robotfilepath = sm.generateResuspendDws(int(argsns.resuspend_only), sortby=argsns.resuspend_sortby,
                                                transferAliquotToDestRack=argsns.resuspend_transferaliquot,
                                                transferDestStartIndex=argsns.resuspend_aliqouot_deststartindex,
                                                tranferAliquotVolume=argsns.resuspend_aliqouot_volume,
                                                destformat=argsns.destformat)
        exit()

    #def generateInstructionCsv(self, designfilename=None, modulestopipetfile="auto", rackfilenames=None):
    pipetcsvfilepath = sm.generateInstructionCsv(designfilename=argsns.designfilename,
        modulestopipetfile=argsns.modulestopipetfile,
        pipdatafilenameformat=pipdatafilenameformat, plateconc=argsns.plateconc, reportname=argsns.reportname)
    #def generateRobotFile(self, fromfiles=True, pipetfiles=None, onefileonly=True):
    # fromfiles=False; the data has been saved in the sm StapleMixer object. (self.PipetDataset)
    robotfilepath = sm.generateRobotFile(fromfiles=False, aux_resuspend=argsns.init_resuspend)


    import sys
    sys.stderr.write(robotfilepath)

    #return robotfilepath # argh, i need to do exit(exitstatus), but exitstatus should be an integer :-(

"""

------------------
---- NOTES -------
------------------
The reason I need to insert placeholders multiple times is that when I create
robot file I only insert fields from pipetdata file (row,source-rackname,source-pos,destin-rackname,destin-index,volume,cmd-comment)
Thus, other parts such as
Note that instructions go through pipetinstructionToCmdVars before
    for instruction in pipetdataset:
        cmdnum += 1
        instruction = self.pipetinstructionToCmdVars(instruction)
        instruction["cmdindex"] = cmdnum
        robotfile.write(self.Config["robot"]["cmd-template"] % instruction)


NOTE NOTE: As of feb 2013, defining the volume and which modules to pipette
has not been implemented. It simply does:
modulestopipet = [{"Modulename":modulename,"ul":"5"} for modulename in self.DesignModules.keys()]



Regarding YAML:
It would seem I have some issues getting it to work.
First of, line breaks are tricky
Second, saving parameters does (naturally) not preserve key order of the
config/param file -- it is a dict after all. If you want order, use an ordered dict.

Regarding line breaks and outputting a reasonable looking file:
# YAML scalars: Plain, single-quoted, double-quoted,
# literal |
# folded >
# folded joins two adjacent non-empty lines into one with a space separator.
# Do not use folded.
# " style will insert '\n' escape characters, much like json
# ' style will insert empty lines to indicate line breaks.
# save with default_flow_style=False and default_style='|'
# BUT DAMN, there is almost no documentation on the dump arguments!! GRR!
# It seems they encourage people to subclass their own Dumper and use that
# to select the right formatting options. http://pyyaml.org/ticket/9
# However I have noticed that after the scalar it is possible to add a number and sign to indicate something...

Regarding placeholders for string formatting:
Regarding placeholder insertion:
"{hej}--{der}".format(hej='sa',der='word', extra='door')  >   Ott[94]: 'sa--word'
"%(hej)s--%(der)s" % dict(hej='sa',der='word', extra='door')
Out[96]: 'sa--word'
Both accepts unneeded arguments. And both will throw a KeyError if an argument
for a placeholder is not given,
"{hej}--{der} m {missing}".format(hej='sa',der='word')
KeyError: 'missing'
# All named placeholders must be used :-(
# This makes it hard to vary the number of times that you insert placeholders.
# In other words, if you want to insert placeholders twice into a template,
# that template needs to account for---the current default template from ConfigGenerator expects you
# to insert e.g. cmdheader placeholder twice. First, you replace %(cmdheader)s with %(cmdindex)03d, then you replace %(cmdindex)03d with the actual header.
# If try to directly replace %(cmdheader)s, you will either not have the cmdheader variable (because you expect to insert cmdindex),
# or if you have the cmdheader variable, it will not be formatted correctly when inserted.
# But if it wasn't for that header that needs special formatting,
#  I guess you could use the insertPlaceholders an infinite number of times with no issues.
Regarding using string.format instead of % :
# would this be better if I used "string".format()?
# In that case, the placeholder should look like {placeholdername:format} rather than %(name)format
# you can also use arguments fields, e.g. {variable['item']} or {variable.field}
# http://docs.python.org/2/library/string.html
# From http://stackoverflow.com/questions/5082452/python-string-formatting-vs-format it also states that
# "You can do stuff like re-use arguments, which you can't do with %" -- which is what I need.
# Also see http://www.python.org/dev/peps/pep-3101/ and http://docs.python.org/2/library/string.html#template-strings
EDIT: No, format has the same problem as %. Once you have a placeholder
that looks like %(name)03d or {name:03d}, you have to insert a number next.
Perhaps you could do something where one variable is used to specify the format, e.g.
{{cmdindex}:{headerformat}} and then always use
format(cmdindex="{cmdindex}",headerformat="{headerformat}") when you are not ready to insert, and
format(cmdindex=2,headerformat="03d") when you are ready to insert.
EDIT-EDIT: So, yes it should be totally possible to re-use it over and over in this way.
- just remember to change headerformat in the dict when (or before) you insert the actual cmdindex number.


Legacy epmotion layout
Before editing, this was how I thought the layout was: (proved wrong)
#      TOOLS     151     152    153
#        156     155     154
#        160     161     162

"""

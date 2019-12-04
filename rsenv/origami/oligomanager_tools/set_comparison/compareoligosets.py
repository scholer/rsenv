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
Created on Fri Aug  5 10:52:13 2011

@author: scholer
"""

### This program takes two design oligo-lists and performs a module-aware comparison.
### This extends the functionality provided by OmCompareSets which were not module-aware.
### The OligosetComparator class also includes the function compareDesignVsDbSols whcih
### can compare a design agains data found in a database


import csv
import psycopg2
import glob
import os

class Design:
    """
    Object representation of a design.
    Currently only acts as a container for data read from a cadnano staple-seqs csv export.
    """
    def __init__(self, filepath=None):

        self.Filepath = filepath
        if self.Filepath:
            self.Filename = os.path.basename(self.Filepath)
        # Note: There is a small difference between self.Fields and self.Filefields:
        # self.Fields are "standard fields", e.g. "moduleclass", "sequence", etc.
        # self.FileFields includes non-standard field names, e.g. "Oligo sequence", "Staple name", etc.
        self.FileFields = None
        self.Fields = dict() # This is actually a fieldmap, mapping standard fields to the fields in the file and dataset.
        #self.FieldsMap = None
        self.Dataset = None
        self.Verboselevel = 0


    def make_fieldsmap(self):
        """
        See also:
            epmotion_staplemixer/epmotion_staplemixer.py
            epmotion_staplemixer/fileutils.py:findFieldsByHint()
        """
        searchfields = dict(moduleclass=('moduleclass', 'module', 'color'),
                            sequence=('sequence', 'seq'))
        for searchfield, lookitems in list(searchfields.items()):
            self.Fields[searchfield] = None
            for candidate in lookitems:
                if self.Fields[searchfield] is not None:
                    break
                for filefield in self.FileFields:
                    #print "comparing " + candidate + " with " + filefield
                    if candidate in filefield.lower():
                        self.Fields[searchfield] = filefield
                        break
            if self.Fields[searchfield] is None:
                print("Error, could not find any columns specifying the " + searchfield + " for filename: " + self.Filepath)
                self.AllOK = False # Flag not to continue... Not used?
            if self.Verboselevel > 3:
                print("self.Fields: %s" % self.Fields)


    def parse_csvfile(self, filepath=None):
        """
        Reads a csv file from path and loads the data into self.Dataset
        """
        designfilename = self.Filename
        if filepath is None:
            filepath = self.Filepath
        else:
            self.Filepath = filepath
            self.Filename = os.path.dirname(filepath)
        if not filepath:
            print("No filepath provided, aborting..:!")
            return False
        dataset, filefields = self._read_csvfile_from_file(self.Filepath)
        self.FileFields = filefields
        self.Dataset = dataset

        if self.Verboselevel > 6:
            print("Dataset from file: " + designfilename)
            print(self.Dataset)
        # Find the key specifying the module... (first 'module', then if no 'module' field, search for 'color').
        self.make_fieldsmap()

        # Arrange the data for easier access:
        # Produce whole design set:
        self.Designset = set([row[self.Fields['sequence']] for row in self.Dataset])
        # Prepare a dict with an empty set for every moduleclass:
        self.Modulesets = dict([(row[self.Fields['moduleclass']], set()) for row in self.Dataset])
        self.OligoModules = dict()
        self.OligoInfo = dict() # Map sequence back to info from file/row.
        for row in self.Dataset:
            self.Modulesets[row[self.Fields['moduleclass']]].add(row[self.Fields['sequence']])
            # It should also be easy to find the module of a particular sequence without looping further:
            if row[self.Fields['sequence']] in self.OligoModules:
                print("WARNING: sequence " + row[self.Fields['sequence']] + " is present multiple times.")
                if self.OligoModules[row[self.Fields['sequence']]] != row[self.Fields['moduleclass']]:
                    print("--> AND THE SEQUENCE IS PRESENT IN TWO DIFFERENT MODULES, " + self.OligoModules[row[self.Fields['sequence']]] + " and " + row[self.Fields['moduleclass']])
            self.OligoModules[row[self.Fields['sequence']]] = row[self.Fields['moduleclass']]
            self.OligoInfo[row[self.Fields['sequence']]] = row
        if self.Verboselevel > 5:
            print("Design and module-sets for designfile: " + designfilename)
            print(self.Designset)
            print(self.Modulesets)

        return self


    def _read_csvfile_from_file(self, designfilename):
        """
        Reads a csvfile and returns tuple with:
            (the data as list of dicts, fields)
        """
        with open(designfilename, 'rU') as designfile:
            self.CsvDialect = csv.Sniffer().sniff(designfile.read(1024))
            self.CsvDialect.lineterminator = '\n'  # Override default line terminator as sniffer always reports \r\n (0x0D,0x0A) as the line terminator.
            designfile.seek(0)
            # Important lesson: You DictReader has several more arguments, so you must define dialect=<dialect> for it to work.
            setreader = csv.DictReader(designfile, dialect=self.CsvDialect)
            filefields = setreader.fieldnames
            dataset = [row for row in setreader if len(row)>0]
        return dataset, filefields



class OligosetComparator:

    def __init__(self, designfilenames, verboselevel=1):
        self.Designfilenames = designfilenames
        self.Verboselevel = verboselevel
        self.FileFields = list()
        self.updateDesigns(designfilenames)
        self.AllOK = True

    def updateDesigns(self, designfilenames):
        """
        Update self.Designs to reflect the files read from designfiles.
        """
        self.Designs = [Design(filename) for filename in designfilenames]
        self.parseDesigns()
        return self.Designs


    def parseDesigns(self, designs=None):
        """
        Parse all designs given by <designs>.
        If no design arg is provided, parses self.Designs.
        """
        if designs is None:
            designs = self.Designs
        for design in designs:
            # code moved to design, where it is more logically placed in OOP.
            design.parse_csvfile()
            #designfilename = design.Filename
#        for i,designfilename in enumerate(designfilenames):
#            design = self.Designs[i]
            #design.Filename = designfilename
            # Debugging:
            #print "DEBUGGING:"
            #print designfilename
            #print os.getcwd()



#            design.ModuleField = None
#            for field in setreader.fieldnames:
#                # Find 'seq' header in the dataset:
#                if 'module' in field.lower():
#                    design.ModuleField = field
#                break
#            if design.ModuleField is None:
#                for field in setreader.fieldnames:
#                    # Find 'seq' header in the dataset:
#                    if 'color' in field.lower():
#                        design.ModuleField = field
#                    break
#            if design.ModuleField is None:
#                print "Error, could not find any columns specifying the module(classes) for filename: " + designfilename
#



    def compareDesigns(self):
        """
        Compares self.Designs[0] against self.Designs[1].
        """
        if len(self.Designs) < 2:
            print("compareDesigns() ERROR: self.Designs < 2 - aborting !")
            return
        # Finished parsing the designs, let's do some initial comparison:
        print(self.Designs)
        self.DesignsetIntersection = self.Designs[0].Designset & self.Designs[1].Designset # set.intersection(other_set)
        self.DesignsetSymmetricDifference = self.Designs[0].Designset ^ self.Designs[1].Designset # set.symmetric_difference(other_set)

        # find common module names...
        self.CommonModuleNames = set(self.Designs[0].Modulesets.keys()) & set(self.Designs[1].Modulesets.keys())
        self.NewModuleNames = set(self.Designs[0].Modulesets.keys()) ^ set(self.Designs[1].Modulesets.keys())
        self.UnchangedModules = set()

        self.Designs[0].UniqueModules = set(self.Designs[0].Modulesets.keys()) - set(self.Designs[1].Modulesets.keys())
        self.Designs[1].UniqueModules = set(self.Designs[1].Modulesets.keys()) - set(self.Designs[0].Modulesets.keys())

        for i, design in enumerate(self.Designs):
            # Changes in modules (module names)
            design.UnchangedModules = set()
            design.ChangedModules = set()
            other_design = self.Designs[1] if i == 0 else self.Designs[0]
            print("\n----" + '-'*len("Report for " + design.Filename) + "-"*6)
            print("--- Report for " + design.Filename + " " + "-"*5)
            print("----" + '-'*len("Report for " + design.Filename) + "-"*6)
            print("Compared against: " + other_design.Filename)
            print("Modules in this design: " + ", ".join(sorted(list(design.Modulesets.keys()))))
            print("COMMON/SHARED MODULES (modules found in both designs): {}".format(
                ", ".join(sorted(list(self.CommonModuleNames))) if self.CommonModuleNames else '<none>'))
            print("ADDED MODULES (modules unique to this design, not found in the other design): {}".format(
                sorted(design.UniqueModules) if design.UniqueModules else '<none>'))
            print("REMOVED MODULES (modules in other design not found in this design): {}".format(
                sorted(other_design.UniqueModules) if other_design.UniqueModules else '<none>'))

            print("\nPer oligo sequence changes for common/shared modules:")
            for module in self.CommonModuleNames: # (set(design.Modulesets.keys()) - design.UniqueModules())
                if len(design.Modulesets[module] ^ other_design.Modulesets[module]) == 0:
                    # Edit: Now using symmetric_difference (^) instead of difference (-)
                    design.UnchangedModules.add(module)
                else:
                    design.ChangedModules.add(module)
            if (not design.UniqueModules) and (not design.ChangedModules):
                print("( And all modules in the two designs include identical sets of oligos. Bye! )")
                return
            print("Common/shared modules that are completely unchanged: {}".format(
                ", ".join(sorted(list(design.UnchangedModules))) if design.UnchangedModules else "<none>"))
            print("Common/shared modules with changed oligos in this design: " + ", ".join(sorted(list(design.ChangedModules))))
            #if design.UniqueModules:
            #    print "New (unique) module names/classes in this design:      " + ", ".join(design.UniqueModules)
            #    print "(Removed module classes in this design:                " + ", ".join(other_design.UniqueModules) + ")"
            for module in design.ChangedModules:
                print("+New oligos in module\t" + module + "\t\t (Start pos noted afterwards)")
                print("++ " + "\n++ ".join([oligo +
                    ("\t\t" + "-".join([design.OligoInfo[oligo]['Start'] if 'Start' in design.OligoInfo[oligo] else '',
                                        design.OligoInfo[oligo]['End'] if 'End' in design.OligoInfo[oligo] else '(no-end-info)']))
                    for oligo in (design.Modulesets[module] - other_design.Modulesets[module])]))
                print("-Oligos removed from module: " + module)
                print("-- " + "\n-- ".join([oligo +
                    ("\t\t" + "-".join([other_design.OligoInfo[oligo]['Start'] if 'Start' in other_design.OligoInfo[oligo] else '',
                                        other_design.OligoInfo[oligo]['End'] if 'End' in other_design.OligoInfo[oligo] else '(no-end-info)']))
                    for oligo in (other_design.Modulesets[module] - design.Modulesets[module])]))
            print("")
            if design.UniqueModules:
                print("Further details for the new/unique module-classes in this design:")
            #print "Per oligo sequence changes (unique module classes):"
            for module in design.UniqueModules:
                if module is None:
                    print("Error: module is None. design.UniqueModules is: {}".format(list(design.UniqueModules.keys())))
                    continue
                similar_module = None
                n_best = 0
                for other_module in other_design.UniqueModules:
                    n_common_oligos = len(design.Modulesets[module] & other_design.Modulesets[other_module])
                    if n_common_oligos > n_best:
                        n_best = n_common_oligos
                        similar_module = other_module
                if n_best == len(design.Modulesets[module]) and len(design.Modulesets[module]) == len(other_design.Modulesets[other_module]):
                    print("".join(["Module ", module, " is IDENTICAL TO ", similar_module, " (", str(n_best), " of ", str(len(design.Modulesets[module])), " in common)"]))
                    continue
                if similar_module:
                    print("Module %s is similar to %s (%s of %s in common)" % (module, similar_module, n_best, len(design.Modulesets[module]) ))
                    #print "".join(["Module ", module, " is similar to ", similar_module, " (", str(n_best), " of ", str(len(design.Modulesets[module])), " in common)"])
                    print("+New oligos (%s minus %s):" % (module, similar_module))
                    #print "+New oligos: (" + module + " minus " + similar_module + ")"
                    print("++" + "\n++".join(design.Modulesets[module] - other_design.Modulesets[similar_module]))
                    print("-Removed oligos: ({} minus {})\n--{}\n".format(similar_module,
                            module, "\n--".join(other_design.Modulesets[similar_module] - design.Modulesets[module])))
                #print "-Removed oligos: (" + similar_module + " minus " + module + ")"
                #print "--" +
                #print ""
    # end compareDesigns


    def compareDesignVsDbSols(self, conn):
        # Fetch data from database using conn and compare against designs in self.Designs.
        # More info on psycopg2:
        # -
        #  - http://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL


        if isinstance(conn, str):
            # PS: If psycopg2 throws an psycopg2.OperationalError, just let it fail for now...
            conn = psycopg2.connect(conn)

        cur = conn.cursor() # Use the DictCursor if you want to be able to receive dicts instead of tuples as result.
        sql = """
SELECT sequence_with_mods AS seq, c.name AS rack
FROM om.solutions s
JOIN om.oligos o ON o.id = s.oligo_id
JOIN om.containers c ON c.id = s.rack_id;"""
        cur.execute(sql)
        db_res = cur.fetchall() # returns list of tuples


        # Consider making other oligos_rack datastructure:
        # oligo_racks[<oligo seq>] = dict(<rack name>=[<list with datarows>])
        # e.g. oligo_racks['ATCGTTC'] = {"IDT_1":[datarowdict1,datarowdict2],"DNAtech2":[...] }
        oligo_racks = dict()
        seqs_present_in_multiple_racks = set() # Keeping track of special oligos
        for entry in db_res:
            seq = entry[0]
            rackname = entry[1]
            if seq not in oligo_racks:
                oligo_racks[seq] = {rackname:[entry]}
            else:
                if rackname in oligo_racks[seq]:
                    oligo_racks[seq][rackname].append(entry)
                else:
                    oligo_racks[seq][rackname] = [entry] # Caveat: If you do list(row), you will get a list with row.keys() !!


        db_oligos = dict()
        # Currently, just let the value be the number of oligo-solutions with that sequence...
        for entry in db_res:
            seq = entry[0]
            rack = entry[1]
            #racks.add(entry[1])
            if seq in db_oligos:
                # I used to just keep count of how many sols/racks/pos are the particular sequence found in.
                #db_oligos[seq].append(rack)
                db_oligos[seq] += (rack,)
            else:
                db_oligos[seq] = (rack,) # Using tuple not list so we can hash it for our set
        # Let's be explicit, just to be safe...
        cur.close()
        conn.close()

        # Now that I have a proper oligo_racks datastructure, I can just use:
        self.compareDesignsVsSeqencesInRackdata(oligo_racks, self.Designs)#, oligo_racks.keys())

        # Old way of doing things (I have split the comparison part out to separate function...
        self.compareDesignVsOligosOld(db_oligos)


    def compareDesignVsOligosOld(self, db_oligos, designs=None):
        """ Old way of doing the comparison """
        if designs is None:
            designs = self.Designs

        racks = set()
        rack_oligo_count = dict()
        for design in self.Designs:
            modulefield = design.Fields['moduleclass']
            sequencefield = design.Fields['sequence']
            print("\ncompareDesignVsOligosOld():\nComparing design " + design.Filename + " against oligomanager database...")
            print("The following rows were not detected in the database:")
            print("\t".join(design.FileFields)) # print headers:
            for row in design.Dataset: # list of dicts...
                if row[sequencefield] not in db_oligos:
                    #print " - " + "\t".join(row.values()) # Random order...
                    print(" - " + "\t".join([row[field] for field in design.FileFields])) # Same order as the file...
                else:
                    oligo_rack = db_oligos[row[sequencefield]][0] # Just take the first rack in the rack tuple.
                    racks.add(oligo_rack)
                    if oligo_rack in rack_oligo_count:
                        rack_oligo_count[oligo_rack] += 1
                    else:
                        rack_oligo_count[oligo_rack] = 1
        print("The rest of the oligos in the design were found in the following racks:")
        print("\n".join([key + " (" + str(val) + ")" for key,val in list(rack_oligo_count.items())]))



    def compareDesignVsRackfiles(self, designfilenames=None, rackfilenames=None):
        """ Compare a design in self.Designs against rackfiles.
            If rackfiles are not given, glob the current directory after *.rack.csv files.
            If designfilenames are not given, use designs in self.Designs. If these are not found
            either, then glob for *.smmc files.
            PS: This is actually compatible with passing multiple designfiles, as indicated by the name.
            Note: You may want to consolidate this with compareDesignVsDb !!
        """

        # 1) READ RACK DATA and make oligo_racks DATASTRUCTURE:
        # Copy/paste a lot from epmotion_staplemixer:
        if rackfilenames is None:
            ext = ".rack.csv"
            #rackfilenames = [fname for fname in os.listdir(os.getcwd()) if fname[len(fname)-len(ext):] == ext] # filter
            rackfilenames = glob.glob("*.rack.csv")
            print("Rackfiles: {0}".format(rackfilenames))
        # Make rackdata structure:
        # keys are rackfilename, e.g. Rackdata["IDT_2013_1-96"]= [ list where each entry is a list of values in for every line in the rack file ]
        self.Rackdata = dict()
        for rackfilename in rackfilenames:
            with open(rackfilename, 'rU') as rackfile:
                # First do some sniffing...
                # Edit: I expect input smmc file to have headers!
                snif = csv.Sniffer()
                csvdialect = snif.sniff(rackfile.read(1024))
                csvdialect.lineterminator = '\n' # Ensure correct line terminator (\r\n is just silly...)
                rackfile.seek(0) # Reset file
                # Then, extract dataset:
                setreader = csv.DictReader(rackfile, dialect=csvdialect)
                # Import data
                # Note: Dataset is a list of dicts.
                self.Rackdata[rackfilename] = [row for row in setreader if len(row)>0]
                rackfileseqfield = self.findFieldByHint(list(self.Rackdata[rackfilename][0].keys()), "seq")
                for row in self.Rackdata[rackfilename]:
                    # Create new field or override existing:
                    row["Sequence"] = row[rackfileseqfield].strip().replace(" ", "")
        # Convert Rackdata structure to a more readily accessible data structure, oligo_racks:
        # oligo_racks is similar to db_oligos in compareDesignVsDbSols, except:
        # oligo_racks[<oligo seq>] = dict(<rack name>=[<list with datarows>])
        # e.g. oligo_racks['ATCGTTC'] = {"IDT_1":[datarowdict1,datarowdict2],"DNAtech2":[...] }

        # Also based on epmotion_staplemixer code:
        oligo_racks = dict()
        seqs_present_in_multiple_racks = set() # Keeping track of special oligos
        for rackname,rackdata in list(self.Rackdata.items()):
            rackname = self.removeFileExt(rackname, (".rack.csv", ".csv")) # Nice to have...
            seqfield = "Sequence" # C.f. the row["Sequence"] hardcoded definition above.
            for row in rackdata:
                seq = row[seqfield]
                if seq not in oligo_racks:
                    # New sequence, just add it:
                    oligo_racks[seq] = {rackname:[row]}
                else:
                    #print "VERBOSE: Sequence in multiple racks ({0}, {1}): {2}".format(rackname, oligo_racks[seq].keys(), seq)
                    # Sequence already exists, i.e. it is found in multiple racks (or multiple positions in the same rack, or both)
                    if rackname in oligo_racks[seq]:
                        # sequence is present in multiple positions in the same rack... weird, but I should be able to handle it.
                        oligo_racks[seq][rackname].append(row)
                        #print "DEBUG: rackname in oligo_racks[seq]"
                    else:
                        oligo_racks[seq][rackname] = [row] # Caveat: If you do list(row), you will get a list with row.keys() !!
        # Finished making oligo_racks data structure from racks

        # 2) Make sure we have design data:
        if designfilenames:
            # Designs are given, we need to update...
            designs = self.updateDesigns(designfilenames)
        else:
            if self.Designs:
                designs = self.Designs
            else:
                designs = self.updateDesigns(glob.glob('*.smmc'))

        # 3) Do comparison of each design and the rackfile data:
        #print oligo_racks
        self.compareDesignsVsSeqencesInRackdata(oligo_racks, designs)#, self.Rackdata.keys())


    def compareDesignsVsSeqencesInRackdata(self, oligo_racks, designs=None ,racknames=None):
        """ Splitting compareDesignVsRackfiles into two parts, continuing from where I left:
            designs as found in self.Designs
            oligo_racks data structure as produced by compareDesignVsRackfiles, i.e.
              oligo_racks[<oligo seq>] = dict(<rack name>=[<list with datarows>])
              e.g. oligo_racks['ATCGTTC'] = {"IDT_1":[datarowdict1,datarowdict2],"DNAtech2":[...] }
            rackdata is mostly used to get racknames...
        """
        if designs is None:
            if self.Designs:
                designs = self.Designs
            else:
                designs = self.updateDesigns(glob.glob('*.smmc'))
        if racknames is None:
            # From: http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
            # There is also a faster alternative using itertools.chain.from_iterable()
            racknames = set([rackname for k,entry in list(oligo_racks.items()) for rackname in list(entry.keys())])

        for design in designs:
            # rack_oligo_count is used to keep track of how many oligos were used from each rack.
            rack_oligo_count = dict() # dict(name=count_of_oligos_used)
            # Used to keep track of any oligos used that are present in multiple racks.
            seqs_present_in_multiple_racks = set()
            # Print
            flag_beSilent = False
            modulefield = design.Fields['moduleclass']
            sequencefield = design.Fields['sequence']
            print("\nComparing design '{0}' against oligos in racks: {1}".format(
                design.Filename, racknames))
#                design.Filename, rackfiles=", ".join(racknames))
            print("1) The following rows in the design file were not found in the racks:")
            print("\t".join(design.FileFields)) # print headers:
            # The actual parsing here is a little different from compareDesignVsDbSols:
            # because there I expected a sequence to be in one and only one rack.
            # Here I take into account that each sequence might be in several racks
            oligos_not_found = 0
            for row in design.Dataset: # list of dicts...
                seq = row[sequencefield]
                #print seq
                if seq not in oligo_racks:
                    #print " - " + "\t".join(row.values()) # Random order...
                    oligos_not_found += 1
                    print(" - " + "\t".join([row[field] for field in design.FileFields])) # Same order as the file...
                else:
                    # For this purpose, I just want to keep count of how many oligos were used from each rack:
                    racks_for_present_seq = list(oligo_racks[seq].keys())
                    if len(racks_for_present_seq) > 1:
                        seqs_present_in_multiple_racks.add(seq)
                        for rackname in racks_for_present_seq:
                            pass # I could do something here, but I chose just to do it later...
                    else:
                        # Sequence is only in one rack, just do regular counting:
                        rackname = racks_for_present_seq[0]
                        if racks_for_present_seq[0] in rack_oligo_count:
                            # Rack already counted at least once:
                            rack_oligo_count[rackname] += 1
                        else:
                            # Rack not counted before. Rackname must be added to counter and value set to 1.
                            rack_oligo_count[rackname] = 1
            print("Totalling {0} oligos that were not found.".format(oligos_not_found))
            print("2a) The following oligo sequences are found in multiple racks: {0}".format(
                "(none)" if len(seqs_present_in_multiple_racks) < 1 else ""))
#            if len(seqs_present_in_multiple_racks) < 1:
#                print " (none of the oligos in the design are found in multiple racks)"
            #print "\n".join([key + " (" + str(val) + ")" for key,val in rack_oligo_count.items()])
            for seq in seqs_present_in_multiple_racks:
                print(" - {0} : [{1}]".format(seq,
                    ["{0} ({1})".format(rackname,len(rackdatarows))
                    for rackname,rackdatarows in list(oligo_racks[seq].items())]))
                #for rackname,rackdatarows in oligo_racks[seq].items():
                #    print "{0}: {1}".format(rackname, rackdatarows)
            print("2b) The rest of the oligos in the design were found in the following racks:")
            # Which code line is more readable: (last line is oldest;
            # when I really wanted to minimalize my code. At present, I prefer readability.
            for rackname,count in list(rack_oligo_count.items()):
                print("{0} ({1})".format(rackname,count))
            #print "\n".join(["{0} ({1})".format(rackname,count) for rackname,count in rack_oligo_count.items()])
            #print "\n".join([key + " (" + str(val) + ")" for key,val in rack_oligo_count.items()])




    # Copy/paste helper methods from epmotion_staplemixer:
    def findFieldByHint(self, candidates, hints):
        """ From epmotion_staplemixer.py
            Used to select a particular candidate determined from a hint,
            e.g. hint "seq" will find "Sequence" in candidates ("Rack","Sequence","Start")
        """
        if not isinstance(hints, (list, tuple)):
            hints = (hints,)
        for hint in hints:
            for candidate in candidates:
                if hint in candidate.lower():
                    return candidate
        # None of the hints were found in either of the options.
        return None
    def removeFileExt(self, filename, extcandidates):
        for candidate in extcandidates:
            if candidate in filename:
                return filename[:len(filename)-len(candidate)]






##################################################
########## USABILITY SHORTCUTS ###################
##################################################

def comparedesignfiles(designfilenames):
    oc = OligosetComparator([designfilenames], verboselevel=0)
    if not oc.AllOK:
        print("oc.AllOK is false, aborting...")
        return
    print("{0}: doing OligosetComparator.compareDesigns() with designfiles: {1}, {2}".format(
      "compareoligosets.py",args.design1filename, args.design2filename))
    oc.compareDesigns()

def compareDesignVsDb(designfilename, conn_string):
    import getpass
    oc  = OligosetComparator([designfilename])
    if not oc.AllOK:
        print("oc.AllOK is false, aborting...")
        return
    #conn_string = "host=10.14.40.243 user=postgres dbname=oligomanager"
    # getpass is a more proper alternative to python 2's input_raw(<prompt>) function.
    if not "password" in conn_string:
        dbpass = getpass.getpass("Please enter password for oligomanager database: ")
        if dbpass: conn_string = conn_string + " password=%s" %dbpass
    oc.compareDesignVsDbSols(conn=conn_string)

def compareDesignVsRackfiles(designfilename, rackfiles=None):
    oc  = OligosetComparator([designfilename])
    if not oc.AllOK:
        print("oc.AllOK is false, aborting...")
        return
    oc.compareDesignVsRackfiles()




if __name__ == "__main__":
    import argparse

    # Get run-time options as a dict
    #options = getRuntimeOptions()

    argparser = argparse.ArgumentParser(description='This script is used to compare the oligo-sets in two origami designs. The script is module-aware, meaning it will first sort the oligos by module (or color!) and then examine the difference between the modules.')
    argparser.add_argument('design1filename', help="Compare this oligo-list..." )
    argparser.add_argument('design2filename', help="...against this." )

    #argparser.add_argument('--stdout', action='store_true', help="Print output to standard out instead of a file.")
    #argparser.add_argument('--writefile', default=None, help="Specify a filename to use for the output. If none is specified, '.mc' is appended to the given input file name.")
    #argparser.add_argument('--verboselevel', default=3, type=int, help="Specify how verbose you want to run the program.")

    args = argparser.parse_args()

#    if args.stdout:
#        # If using stdout, we need to supress all other prints completely.
#        verboselevel = -1
#    else:
#        verboselevel = args.verboselevel


    oc  = OligosetComparator([args.design1filename, args.design2filename], verboselevel=6)
    if oc.AllOK:
        print("{0}: doing OligosetComparator.compareDesigns() with designfiles: {1}, {2}".format(
          "compareoligosets.py",args.design1filename, args.design2filename))
        oc.compareDesigns()
    else:
        print("oc.AllOK is false, aborting...")

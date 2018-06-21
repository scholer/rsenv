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
# pylint: disable-msg=C0111,W0613,W0621


import pytest
from StringIO import StringIO
import os
import glob

## Logging:
import logging
logger = logging.getLogger(__name__)
#logging.getLogger("__main__").setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logging.getLogger("staplemixer.utils.make_24rack_specs_for_flat_oligolist").setLevel(logging.DEBUG)
logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s\n"
logging.basicConfig(level=logging.INFO, format=logfmt)


#########################
### System Under Test ###
#########################

#import staplemixer.utils.rackfileutils as rackfileutils
from rspyutilslib.oligodatalib import rackfileutils
#from staplemixer.utils.rackfileutils import \
#        read_monolithic_rackfile, read_rackfilehandle



@pytest.fixture
def monolithic_rackfile_string_manyfields():
    rackstring = """\
Plate Name,Payment Method,Plate Barcode,Sales Order #,Reference #,Well Position,Sequence Name,Sequence,Manufacturing ID,Measured Molecular Weight,Calculated Molecular Weight,OD260,nmoles,µg,Measured Concentration µM ,Final Volume µL ,Extinction Coefficient L/(mole·cm),Tm,Well Barcode
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160157,A01,TRPJ:col1011v6:12[199],GTA GCA CCA TTA CCA TGC CAG CAA,167855657,7290.6,7291,6.15,26.25,191,100.19,262,234300,59.81,
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160158,B01,TRPJ:col1011v6:13[192],AAT CAC CAT TTT AAT AGA AAA TTC ATA TTT ATT TTG,167855658,11004.5,11005,10.34,28.56,314,99.86,286,361900,52.3,
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160159,C01,TRPJ:col1011v6:14[175],AGC GCC AAC CAT TTG GGA ATT AGA TAG CAA GGC CGG AAA C,167855659,12371.8,12372,9.8,24.38,302,99.92,244,401700,68.07,
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160160,D01,TRPJ:col1011v6:15[192],TCA CAA TCC CGA GGA AAC GCA ATA ATG AAA TA,167855660,9827.2,9827,8.93,26.84,264,100.15,268,332500,59.94,
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160161,E01,TRPJ:col1011v6:16[175],ATA CCC AAA CAC CAC GGA ATA AGT GGT TTA CC,167855661,9769.7,9770,8.77,27.48,269,99.93,275,319100,61.53,
TRPJ_Dec2013_02_97-192,929227-83140,8021777,2280165,66160162,F01,TRPJ:col1011v6:17[192],GCA ATA GCA GAG AAT AAC ATA AAA ACA GCC AT,167855662,9859.8,9861,8.34,24.46,241,99.84,245,341100,57.9,
TRPJ-Dec2013_1_1-96,929227-83140,8021778,2280165,66160064,A01,TRPJ:col07v6:0[135],TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG,167856181,9872.4,9872,8.31,25.57,252,99.88,256,325000,59.83,
TRPJ-Dec2013_1_1-96,929227-83140,8021778,2280165,66160065,B01,TRPJ:col07v6:1[128],CCT CAA GAT GAA AGT ATT AAG AGG CTT TCC AG,167856182,9856,9856,8.94,27.89,275,99.96,279,320600,58.58,
TRPJ-Dec2013_1_1-96,929227-83140,8021778,2280165,66160066,C01,TRPJ:col07v6:2[111],ACG TTA GTT CTA AAG TTT TGT CGT CTG AGA CT,167856183,9834.3,9835,8.04,26.18,257,99.92,262,307300,59.1,
TRPJ-Dec2013_1_1-96,929227-83140,8021778,2280165,66160067,D01,TRPJ:col07v6:3[128],TGC CTT GAG GTA ATA AGT TTT AAC TGC GCC GA,167856184,9854.1,9854,8.96,29.03,286,100.1,290,308500,62.8,
"""
    return rackstring

@pytest.fixture
def monolithic_rackfile_string():
    rackstring = """\
Plate Name, Well Position, Sequence Name, Sequence
TRPJ_Dec2013_02_97-192, A01, TRPJ:col1011v6:12[199], GTA GCA CCA TTA CCA TGC CAG CAA
TRPJ_Dec2013_02_97-192, B01, TRPJ:col1011v6:13[192], AAT CAC CAT TTT AAT AGA AAA TTC ATA TTT ATT TTG
TRPJ_Dec2013_02_97-192, D05, TRPJ:col1213v6:31[200], CTA AAC AGG AGG CCG AAT TCA CCA
TRPJ-Dec2013_1_1-96, A01, TRPJ:col07v6:0[135], TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG
TRPJ-Dec2013_1_1-96, B01, TRPJ:col07v6:1[128], CCT CAA GAT GAA AGT ATT AAG AGG CTT TCC AG
TRPJ-Dec2013_1_1-96, C12, TRPJ:col14-21v6:31[296], GTC TGT CCA TCA CGC ACA ATA TTA C
TRPJ-Dec2013_1_1-96, D12, TRPJ:col14-21v6:31[328], AAT ACT TCT TTG ATT ACA AAC TAT
"""
    return rackstring

@pytest.fixture
def temp_monolithic_rackfile(monolithic_rackfile_string):
    pass

@pytest.fixture
def monolithic_rackfilehandle(monolithic_rackfile_string):
    fh = StringIO(monolithic_rackfile_string)
    return fh

@pytest.fixture
def monolithic_rackdata():
    rows = [{'Sequence Name': 'TRPJ:col1011v6:12[199]', 'Sequence': 'GTA GCA CCA TTA CCA TGC CAG CAA', 'Well Position': 'A01', 'Plate Name': 'TRPJ_Dec2013_02_97-192'},
        {'Sequence Name': 'TRPJ:col1011v6:13[192]', 'Sequence': 'AAT CAC CAT TTT AAT AGA AAA TTC ATA TTT ATT TTG', 'Well Position': 'B01', 'Plate Name': 'TRPJ_Dec2013_02_97-192'},
        {'Sequence Name': 'TRPJ:col1213v6:31[200]', 'Sequence': 'CTA AAC AGG AGG CCG AAT TCA CCA', 'Well Position': 'D05', 'Plate Name': 'TRPJ_Dec2013_02_97-192'},
        {'Sequence Name': 'TRPJ:col07v6:0[135]', 'Sequence': 'TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG', 'Well Position': 'A01', 'Plate Name': 'TRPJ-Dec2013_1_1-96'},
        {'Sequence Name': 'TRPJ:col07v6:1[128]', 'Sequence': 'CCT CAA GAT GAA AGT ATT AAG AGG CTT TCC AG', 'Well Position': 'B01', 'Plate Name': 'TRPJ-Dec2013_1_1-96'},
        {'Sequence Name': 'TRPJ:col14-21v6:31[296]', 'Sequence': 'GTC TGT CCA TCA CGC ACA ATA TTA C', 'Well Position': 'C12', 'Plate Name': 'TRPJ-Dec2013_1_1-96'},
        {'Sequence Name': 'TRPJ:col14-21v6:31[328]', 'Sequence': 'AAT ACT TCT TTG ATT ACA AAC TAT', 'Well Position': 'D12', 'Plate Name': 'TRPJ-Dec2013_1_1-96'}]
    return rows


@pytest.fixture
def racksdata_sample():
    racksdata = {'TRPJ-Dec2013_1_1-96': [{'Plate Name': 'TRPJ-Dec2013_1_1-96',
   'Sequence': 'TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG',
   'Sequence Name': 'TRPJ:col07v6:0[135]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'A01'},
  {'Plate Name': 'TRPJ-Dec2013_1_1-96',
   'Sequence': 'CCT CAA GAT GAA AGT ATT AAG AGG CTT TCC AG',
   'Sequence Name': 'TRPJ:col07v6:1[128]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'B01'},
  {'Plate Name': 'TRPJ-Dec2013_1_1-96',
   'Sequence': 'GTC TGT CCA TCA CGC ACA ATA TTA C',
   'Sequence Name': 'TRPJ:col14-21v6:31[296]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'C12'},
  {'Plate Name': 'TRPJ-Dec2013_1_1-96',
   'Sequence': 'AAT ACT TCT TTG ATT ACA AAC TAT',
   'Sequence Name': 'TRPJ:col14-21v6:31[328]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'D12'}],
 'TRPJ_Dec2013_02_97-192': [{'Plate Name': 'TRPJ_Dec2013_02_97-192',
   'Sequence': 'GTA GCA CCA TTA CCA TGC CAG CAA', 'nmoles':'30', u'Final Volume µL ': '200',
   'Sequence Name': 'TRPJ:col1011v6:12[199]',
   'Well Position': 'A01'},
  {'Plate Name': 'TRPJ_Dec2013_02_97-192',
   'Sequence': 'AAT CAC CAT TTT AAT AGA AAA TTC ATA TTT ATT TTG',
   'Sequence Name': 'TRPJ:col1011v6:13[192]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'B01'},
  {'Plate Name': 'TRPJ_Dec2013_02_97-192',
   'Sequence': 'CTA AAC AGG AGG CCG AAT TCA CCA',
   'Sequence Name': 'TRPJ:col1213v6:31[200]', 'nmoles':'30', u'Final Volume µL ': '200',
   'Well Position': 'D05'}]}
    return racksdata

def test_read_rackfile(monkeypatch, monolithic_rackdata):
    #racks = {row['Plate Name'] for row in monolithic_rackdata}
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'racksplitter')
    monkeypatch.chdir(test_data_dir)
    fn = glob.glob(test_data_dir+'/*.allracks.csv')[0]
    logger.info("Using file: %s", fn)
    csvdata = rackfileutils.read_rackfile(fn)
    csvdata = list(csvdata)
    assert set(csvdata[0].keys()) == set(monolithic_rackdata[0].keys())
    assert csvdata == monolithic_rackdata

def test_read_monolithic_rackfile(monkeypatch, monolithic_rackdata):
    #def mockreader(fh):
    #    return monolithic_rackdata
    #monkeypatch.setattr(rackfileutils, 'read_rackfilehandle', mockreader)
    # Not really much reason to test...
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'racksplitter')
    monkeypatch.chdir(test_data_dir)
    fn = glob.glob(test_data_dir+'/*.allracks.csv')[0]
    logger.info("Using file: %s", fn)
    rackdata = rackfileutils.read_monolithic_rackfile(fn)
    racks = {row['Plate Name'] for row in monolithic_rackdata}
    assert set(rackdata.keys()) == racks

def test_read_rackfilehandle(monkeypatch, monolithic_rackdata, monolithic_rackfilehandle):
    """
    rackdata[platename] = [list of dicts]
    """
    rackdata = rackfileutils.read_rackfilehandle(monolithic_rackfilehandle)
    racks = {row['Plate Name'] for row in monolithic_rackdata}
    #teststruct =
    #print "rackdata: %s" % rackdata
    print "rackdata.keys(): %s" % rackdata.keys()
    #print "monolithic_rackdata[0].keys(): %s" % monolithic_rackdata[0].keys()
    assert set(rackdata.keys()) == {'TRPJ_Dec2013_02_97-192', 'TRPJ-Dec2013_1_1-96'}
    assert set(rackdata.keys()) == racks
    print rackdata['TRPJ-Dec2013_1_1-96']
    assert set(rackdata['TRPJ-Dec2013_1_1-96'][0].keys()) == set(monolithic_rackdata[0].keys())
    assert rackdata['TRPJ-Dec2013_1_1-96'][0]['Sequence'] == 'TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG'

def test_read_rackfilehandle_xls():
    with open(os.path.join(os.path.dirname(__file__), 'test_data', 'idt_espec_2287646.xls')) as fd:
        # datastructure: rackdata[<rackname>] = [list of rows]
        rackdata = rackfileutils.read_rackfilehandle(fd)
    seqs = [("TR-SS_IDT2014-col12-13_193-", ("TTC GGA ACC TGA GAC TCC TCA AGA", "AGC ATT GAT GAT ATT CAC AAA CAA CTG CCT AT")),
            ("TR-SS_IDT2014-col7-11_97-192", ("TAT AAG TAT AGC CCG GAA TAG GTG TAT CAC CG", "TTT GTC GTG ATA CAG GAG TGT ACT ATA CAT GG")),
            ("TR-SS_IDT2014-col1-6_0-96", ("CCA TGT ACA GGG ATA GCA AGC CCA", "CGT TGA AAG AAT TGC GAA TAA TAA TTT TAT AGG AAC"))
            ]
    for rack, seqs in seqs:
        for i, seq in enumerate(seqs):
            assert rackdata[rack][i]['Sequence'] == seq



def test_write_rackdata(racksdata_sample):
    """
    Sorts rackdata and writes to filehandle.
    write_rackdata(filehandle, rackdata, sortby=None, dialect=None):
    """
    filehandle = StringIO()
    rackfileutils.write_rackdata(filehandle, racksdata_sample['TRPJ-Dec2013_1_1-96'])
    print filehandle.tell()
    assert filehandle.tell() == 435

def test_filter_racksdata(racksdata_sample):
    racksdata = rackfileutils.filter_racksdata(racksdata_sample)
    rackdata = next(iter(racksdata.values()))
    row = next(iter(rackdata))
    assert set(row.keys()) == set( ('Pos', 'Name', 'Sequence', 'nmoles') )
    assert ' ' not in row['Sequence']
    print row['Sequence']
    assert all(x.upper() in 'ATGC' for x in row['Sequence'])

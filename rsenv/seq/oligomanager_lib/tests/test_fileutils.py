#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2013 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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
##
# pylint: disable-msg=C0111,W0613,W0621


import os
from StringIO import StringIO

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

from rspyutilslib.filedatalib.fileutils import gen_input_filehandles, \
            gen_csv_data, gen_csv_datasets, \
            findFieldByHint, removeFileExt, natural_sort



def test_findFieldByHint():
    assert findFieldByHint(['Pos', 'Sequence', 'Volume'], 'seq') == 'Sequence'
    candidates1 = "Sequence, Length, Pos".split(', ')
    assert findFieldByHint(candidates1, "len") == "Length"
    candidates = "Sequence Name, Sequence, Manufacturing ID, Measured Molecular Weight, Calculated Molecular Weight, OD260, nmoles, µg, Measured Concentration µM , Final Volume µL , Extinction Coefficient L/(mole·cm), Tm, Well Barcode".split(', ')
    assert findFieldByHint(candidates, ('sequence', 'seq')) == "Sequence"



def test_removeFileExt():
    assert removeFileExt('file.rack.csv', ('.txt', '.rack.csv', '.csv')) == 'file'


def test_natural_sort():
    assert natural_sort(['Pos', 'Sequence', 'Volume']) == ['Pos', 'Sequence', 'Volume']
    assert natural_sort(['pos', 'Sequence', 'volume']) == ['pos', 'Sequence', 'volume']
    assert natural_sort(['Sequence', 'pos', 'volume']) == ['pos', 'Sequence', 'volume']
    assert natural_sort(['Rack1', 'Rack10', 'Rack2'])  == ['Rack1', 'Rack2', 'Rack10']



def test_gen_input_filehandles():
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'resuspend_tubes')
    filenames = ( os.path.join(test_data_dir, filename) for filename in ('flat_oligo_list.csv', ) )
    filehandles = gen_input_filehandles(filenames)
    assert next(filehandles).name == os.path.join(test_data_dir, 'flat_oligo_list.csv')


def test_gen_csv_data(monkeypatch):
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'resuspend_tubes')
    monkeypatch.chdir(test_data_dir)
    with open('flat_oligo_list.csv') as filehandle:
        filedata = gen_csv_data(filehandle)
        row = next(filedata)
        assert row['oligo_name'] == 'dscM13v1:0->31'
        assert row['Sequence'] == 'GAAAGCGAAAGGAGCGGGCGCTAGGGCGCTGG'
        assert row['nmoles'] == '26.27'
        assert float(row['nmoles']) == 26.27


def test_gen_csv_datasets(monkeypatch):
    """
    Generates datasets from a sequence of inputfilehandles.
    """
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'resuspend_tubes')
    monkeypatch.chdir(test_data_dir)
    testdata1 = """\
oligo_name,Sequence,nmoles
dscM13v1:0->31,GAAAGCGAAAGGAGCGGGCGCTAGGGCGCTGG,26.27
"""
    testdata2 = """\
oligo_name,Sequence,nmoles
dscM13v1:32->55,GATAACTATGCTGAATGTTGACAG,30
"""
    filehandles = [StringIO(buff) for buff in (testdata1, testdata2) ]
    print filehandles
    csv_datasets = gen_csv_datasets(filehandles)
    filedata = next(csv_datasets)
    row = next(filedata)
    print ", ".join(i for i in row)
    assert row['oligo_name'] == 'dscM13v1:0->31'
    assert row['Sequence'] == 'GAAAGCGAAAGGAGCGGGCGCTAGGGCGCTGG'
    assert row['nmoles'] == '26.27'
    assert float(row['nmoles']) == 26.27
    filedata = next(csv_datasets)
    row = next(filedata)
    print ", ".join(i for i in row)
    assert row['oligo_name'] == 'dscM13v1:32->55'
    assert row['Sequence'] == 'GATAACTATGCTGAATGTTGACAG'
    assert row['nmoles'] == '30'
    assert float(row['nmoles']) == 30.0

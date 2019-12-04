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


import os


############################
## System under test: SUT ##
############################
from rsenv.origami.oligomanager_lib.rsoligoutil.make_24rack_specs_for_flat_oligolist import \
        gen_calculated_resuspend_data, gen_calculated_resuspend_datasets, \
        split_data, gen_input_filenames

#######################
## Dependent modules ##
#######################
from rsenv.origami.oligomanager_lib.filedatalib.fileutils import gen_input_filehandles, gen_csv_datasets, writecsvdatasetstofiles


## Logging:
import logging
logger = logging.getLogger(__name__)
#logging.getLogger("__main__").setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logging.getLogger("epmotion_staplemixer.utils.make_24rack_specs_for_flat_oligolist").setLevel(logging.DEBUG)
logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s\n"
logging.basicConfig(level=logging.INFO, format=logfmt)




def test_gen_input_datafilenames():
    filenames = gen_input_filenames()
    assert next(filenames) == 'flat_oligo_list.csv'



def test_gen_calculated_resuspend_data():
    test_data = ( dict(oligo_name='test_oligo', Sequence='AGTC', nmoles='100') for i in xrange(2) )
    calculated_data = gen_calculated_resuspend_data(test_data)
    row = next(calculated_data)
    assert row['oligo_name'] == 'test_oligo'
    assert row['Sequence'] == 'AGTC'
    assert row['nmoles'] == '100'
    assert float(row['nmoles']) == 100
    assert row['final_vol_ul'] == 100/100*1000 # V=n/c, n=100, c=100, but nmol/uM = ml, so multiply with 1000 to get ul.
    assert row['Pos'] == 'A01'
    row = next(calculated_data)
    assert row['Pos'] == 'A02'

def test_gen_calculated_resuspend_datasets():
    pass


def test_split_data():
    # split_data returns an itertools.izip_longest object, which is not equal to a normal generator object.
    test_data = [i for i in xrange(10)]
    res_tup = ( (0, 1), (2, 3), (4, 5), (6, 7), (8, 9) )
    assert list(split_data((i for i in test_data), 2)) == list(res_tup )
    assert list(split_data(test_data, 2, generator_input=False)) == list(res_tup )

def test_writetofiles():
    pass

def test__writefile():
    pass



def test_all(monkeypatch):
    """
    tmpdir fixture is a unique, temporary py.path.local filesystem object

    Argh, shiit. Another thing about using generators: Be mindful, they are not invoked
    until needed. This resulted in some initial jitters:
    1) I changed dir to test_data_dir.
    2) I invoked resuspend_output_data = gen_calculated_resuspend_datasets()
    3) I changed dir to a temporary dir.
    4) I invoked writetofiles(resuspend_output_data)
    When using lists, gen_calculated_resuspend_datasets would have read the data before I
    switched to the temporary directory.
    However, since I was using generators, the datasets created with gen_calculated_resuspend_datasets
    were not created until I invoked writetofiles(resuspend_output_data) - after I had changed
    the current working directory to the tmpdir.

    """
    script_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(script_dir, 'test_data', 'resuspend_tubes')
    monkeypatch.chdir(test_data_dir)
    logger.info("os.getcwd(), before gen_calculated_resuspend_datasets: %s", os.getcwd())
    # default is dictated by gen_input_filenames().
    inputfiles = gen_input_filenames()
    inputfilehandles = gen_input_filehandles(inputfiles)
    datasets = gen_csv_datasets(inputfilehandles)
    resuspend_output_data = gen_calculated_resuspend_datasets(datasets)
    #monkeypatch.chdir(tmpdir)
    logger.info("os.getcwd(): %s", os.getcwd())
    writecsvdatasetstofiles(resuspend_output_data)

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


import pytest
import tempfile

import os
import glob
import yaml
import StringIO

## SUT:
from staplemixer.staplemixer import StapleMixer
#from epmotion_staplemixer import epmotion_staplemixer


## Logging:
import logging
logger = logging.getLogger(__name__)
#logging.getLogger("__main__").setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logging.getLogger("epmotion_staplemixer.epmotion_staplemixer").setLevel(logging.DEBUG)
logfmt = "%(levelname)s:%(name)s:%(lineno)s %(funcName)s(): %(message)s\n"
logging.basicConfig(level=logging.INFO, format=logfmt)

test_cmd_yaml = """
"cmd-placeit-tips": |2

  [%(cmdindex)03d]
  OpcodeStr=Place it
  Opcode=115
  Bezeichner=
  MatDatei=./top/dws/tips/%(tiptype)s
  MatName=%(tiptype)s
  BehaelterName=%(tiptype)s_%(cmdindex)02d
  EnumMatType=4
  EnumSlotNr=%(slotnr)s
  Stapelindex=0

"""
test_cmd = yaml.load(test_cmd_yaml)



@pytest.fixture
def epmotion_test_config():
    testconfig_filepath = os.path.join(os.path.dirname(__file__), "test_data", "epmotion-cmd-templates.yml")
    epmotion_cmd_templates_testconfig = yaml.load(testconfig_filepath)
    return epmotion_cmd_templates_testconfig

@pytest.fixture()
def tempfiledir():
    newpath = tempfile.mkdtemp()
    return newpath

@pytest.fixture()
def tempfilefile():
    newpath = tempfile.mkstemp() # returns (filenumber, filepath)
    #newpath = tempfile.TemporaryFile() # returns an open file handle
    return newpath

@pytest.fixture
def staplemixer_patched(monkeypatch, epmotion_test_config):
    """
    Returns a epmotion_staplemixer with chdir to the default test_data directory
    and the following patched methods.
     -
    """
    testconfig_filepath = os.path.join(os.path.dirname(__file__), "test_data", "epmotion-cmd-templates.yml")
    #monkeypatch.setattr(epmotion_staplemixer.epmotion_staplemixer.yaml, 'load', epmotion_test_config)
    #monkeypatch.setattr(StapleMixer, 'load', epmotion_test_config)
    monkeypatch.chdir(os.path.dirname(testconfig_filepath)) # Indeed, this is applied for all epmotion_staplemixer calls, I believe.
    sm = StapleMixer()
    monkeypatch.setattr(StapleMixer, '_getReportConcUserInput', lambda *x: '100')
    def fake_write_pipetdata_to_file(*args):
        logger.debug("Intercept pipdata write request (to pipdatafile '%s')", args[1])
        return True
    monkeypatch.setattr(StapleMixer, 'write_pipetdata_to_file', fake_write_pipetdata_to_file)
    return sm


@pytest.fixture
def staplemixer_patchedAll_resuspendtestdir(monkeypatch, epmotion_test_config):
    """
    Returns a epmotion_staplemixer with chdir to the default test_data directory
    and the following patched methods.
     -
    """
    testdir = os.path.join(os.path.dirname(__file__), "test_data", "resuspend_test")
    monkeypatch.chdir(testdir) # Indeed, this is applied for all epmotion_staplemixer calls, I believe.
    sm = StapleMixer()
    monkeypatch.setattr(StapleMixer, '_getReportConcUserInput', lambda *x: '100')
    def fake_write_pipetdata_to_file(*args):
        logger.debug("Intercept pipdata write request (to pipdatafile '%s')", args[1])
        return True
    monkeypatch.setattr(StapleMixer, 'write_pipetdata_to_file', fake_write_pipetdata_to_file)
    def fake_writeStringIOtoFile(*args):
        logger.debug("Intercept robot StringIO write request (to filepath '%s')", args[1])
        return True
    monkeypatch.setattr(StapleMixer, '_writeStringIOtoFile', fake_writeStringIOtoFile)
    return sm


#@pytest.fixture
#def staplemixer_patchedAll_nochdir(request, monkeypatch, epmotion_test_config):
#    """
#    Uses the request object to instrospect the "requesting" test function,
#    c.f. http://pytest.org/latest/fixture.html
#    Unfortunately, I cannot get this to work at the function level...
#    Returns a epmotion_staplemixer with no chdir, but with all file access methods patched:
#    - _getReportConcUserInput
#    - write_pipetdata_to_file
#    - _writeStringIOtoFile
#    """
#    logger.debug("request.function attributes: %s", request.function.__dict__)
#    monkeypatch.chdir(request.function.testdir)
#
#    sm = StapleMixer()
#    monkeypatch.setattr(StapleMixer, '_getReportConcUserInput', lambda *x: '100')
#    def fake_write_pipetdata_to_file(*args):
#        logger.debug("Intercept pipdata write request (to pipdatafile '%s')", args[1])
#        return True
#    monkeypatch.setattr(StapleMixer, 'write_pipetdata_to_file', fake_write_pipetdata_to_file)
#    def fake_writeStringIOtoFile(*args):
#        logger.debug("Intercept robot StringIO write request (to filepath '%s')", args[1])
#        return True
#    monkeypatch.setattr(StapleMixer, '_writeStringIOtoFile', fake_writeStringIOtoFile)
#    return sm


def test_staplemixer_init(staplemixer_patched):

    logger.info("test_cmd_yaml: %s", test_cmd_yaml)
    logger.info("test_cmd['cmd-placeit-tips']: %s", test_cmd["cmd-placeit-tips"])
    sm = staplemixer_patched
    logger.info("sm.CmdTemplates['cmd-placeit-tips']: %s", sm.CmdTemplates["cmd-placeit-tips"])
    assert sm.CmdTemplates["cmd-placeit-tips"] == test_cmd["cmd-placeit-tips"]

def test_insertPlaceholders(staplemixer_patched):
    sm = staplemixer_patched
    pars = dict(cmdindex=3, slotnr=158)
    #test_strings =
    #test_string1 = "cmdindex is: %(cmdindex)s, slotnr is: %(slotnr)s"
    test_string2 = "cmdindex is: %(cmdindex)03d, slotnr is: %(slotnr)s, cmdindex again: %(cmdindex)s"
    assert sm.insertPlaceholders(test_string2, pars) == "cmdindex is: 003, slotnr is: 158, cmdindex again: 3"
    assert sm.insertPlaceholders([test_string2], pars)[0] == "cmdindex is: 003, slotnr is: 158, cmdindex again: 3"
    assert sm.insertPlaceholders(dict(a=test_string2), pars)['a'] == "cmdindex is: 003, slotnr is: 158, cmdindex again: 3"


def test_small_methods_tests(staplemixer_patched):
    # Moved to utils.fileutils
    pass


def test_read_rackfiles(monkeypatch, staplemixer_patched):
    monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    #sm.read_rackfiles() # Is invoked during init...
    assert set(sm.Racknames) == set(filename[:-9] for filename in glob.glob("*.rack.csv"))
    #assert sm.Racknames == glob.glob("*.rack.csv")


def test_read_designfile(monkeypatch, staplemixer_patched):
    monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    designfilename = 'TR.ZZ-FRET-design1-FRET.csv.smmc'
    assert designfilename in os.listdir('.')
    sm.read_designfile(designfilename)
    print sm.DesignSequenceFieldName
    assert sm.DesignSequenceFieldName == 'Sequence'
    assert isinstance(sm.DesignModules, dict)
    assert 'TR:zz-IndexFRET' in sm.DesignModules
    assert set(sm.Racknames) == set(filename[:-9] for filename in glob.glob("*.rack.csv"))





def test_read_modulestopipetfile(monkeypatch, staplemixer_patched):
    """
    StapleMixer.read_designfile must have been invoked first.
    """
    monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    designfilename = 'TR.ZZ-FRET-design1-FRET.csv.smmc'
    sm.read_designfile(designfilename)
    modpipet = sm.read_modulestopipetfile()
    # modpipet data is currently a bit weird:   list of {"Modulename":modulename, "ul":"5"} dicts.
    # Would have been easier to have:           OrderedDict[modulename]=ul
    assert set(modpipet[0].keys()) == set(["Modulename", "ul"])


def test_generateInstructionCsv(staplemixer_patched, monkeypatch):#, tempfiledir):
    monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    designfilename = 'TR.ZZ-FRET-design1-FRET.csv.smmc'
    sm.read_designfile(designfilename)
    #modpipet = sm.read_modulestopipetfile() # is called automatically by generateInstructionCsv
    #monkeypatch.chdir(tempfiledir)
    sm.generateInstructionCsv() # the actual writing should be monkeypatched out in the fixture.




def test_generateRobotFile(staplemixer_patched, monkeypatch):#, tempfiledir):
    monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    designfilename = 'TR.ZZ-FRET-design1-FRET.csv.smmc'
    sm.read_designfile(designfilename)
    #modpipet = sm.read_modulestopipetfile() # is called automatically by generateInstructionCsv
    #monkeypatch.chdir(tempfiledir)
    sm.generateInstructionCsv() # the actual writing should be monkeypatched out in the fixture.
    def fake_writeStringIOtoFile(*args):
        logger.debug("Intercept robot StringIO write request (to filepath '%s')", args[1])
        return True
    monkeypatch.setattr(StapleMixer, '_writeStringIOtoFile', fake_writeStringIOtoFile)
    sm.generateRobotFile(fromfiles=False) # fromfiles=False will read from self.PipetDataset.



def test_generateResuspendDws(staplemixer_patchedAll_resuspendtestdir, monkeypatch):#, tempfiledir):
    #testdir = os.path.join(os.path.dirname(__file__), "test_data", "resuspend_test")
    #monkeypatch.chdir(testdir)
    # staplemixer_patched also invokes monkeypatch.chdir which overrides whatever you do here:
    # I therefore created staplemixer_patchedAll_nochdir fixture
    # However, the present monkeypatch does not apply to that fixture.
    # So, I'm trying to use the "request" fixture argument to retrieve the testdir
    # variable from this test function.
    # However, that didn't work either (AttributeError: 'function' object has no attribute 'testdir')
    # so now I hardcode the chdir to resuspend_test:
    sm = staplemixer_patchedAll_resuspendtestdir
    #designfilename = 'TR.ZZ-FRET-design1-FRET.csv.smmc'
    #sm.read_designfile(designfilename)
    #modpipet = sm.read_modulestopipetfile() # is called automatically by generateInstructionCsv
    #monkeypatch.chdir(tempfiledir)
    #sm.generateInstructionCsv() # the actual writing should be monkeypatched out in the fixture.
    sm.generateResuspendDws(160) # fromfiles=False will read from self.PipetDataset.




#@pytest.mark.skipif(True, reason="Not ready yet")

def test_writeStringIOtoFile(staplemixer_patched, monkeypatch, tempfiledir, tempfilefile):
    """
    Remember to test the method that was monkeypatched out of generateRobotFile:
    """
    #monkeypatch.chdir(os.path.join(os.path.dirname(__file__), "test_data"))
    sm = staplemixer_patched
    monkeypatch.chdir(tempfiledir)
    robotfile = StringIO.StringIO()
    robotfile.write("\n".join("Remember to test the method that was monkeypatched out of generateRobotFile:".split()))
    robotfile.write("\n\nnRemember to test the method that was monkeypatched out of generateRobotFile:")
    sm._writeStringIOtoFile(robotfile, tempfilefile[1])


@pytest.mark.skipif(True, reason="Not ready yet")
def test_XXXX(staplemixer_patched):
    sm = staplemixer_patched

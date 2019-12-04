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


try: import simplejson as json
except ImportError: import json
import yaml

class ConfigGenerator():

    #self.Config = dict()
    def __init__(self):
        # Semantics: method, procedure, program, application, protocol - same same
        # Define what you want here. Use variable-placeholders for things that
        # should be inserted dynamically during program execution.
        self.Labware = {
        "IDT":dict(MatDatei="./top/dws/plates/dwp96/AB_DWP_1200",
                   MatName="AB_DWP_1200",
                   EnumMatType="8"),
        # DNAtech: 96 well tube plate
        "DNAtech":dict(MatDatei="./top/dws/plates/tubes96/MICR_TP_1300_5",
                       MatName="MICR_TP_1300_5",
                       EnumMatType="8"),
        "Axygen":dict(MatDatei="./top/dws/plates/dwp96/AXYG_DWP_600",
                   MatName="AXYG_DWP_600",
                   EnumMatType="8"),
        "modulerack":dict(MatDatei="./top/dws/trth/Rack_1_5ml",
                   MatName="Rack_1_5ml",
                   EnumMatType="512"),
        }
        self.Config = {
        "robot":{

            "cmd-placeit-rack":"""
[%(cmdindex)03d]
OpcodeStr=Place it
Opcode=115
MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
MatName=AXYG_DWP_600
BehaelterName=%(sourcerack)s
EnumMatType=8
EnumSlotNr=%(slotnr)s
Stapelindex=0
RackLevelSensor=0
StartVolumenNanoliter_0=100000
""",
#MatDatei=./top/dws/plates/dwp96/AB_DWP_1200
#MatName=AB_DWP_1200 ; AB_DWP_1200 for IDT plates. For DNAtech plates, use plates/tubes96/MICR_TP_1300_5 labware. For AxyGen use AXYG_DWP_600
#BehaelterName=%(sourcerack)s  # Taken from the *.rack.csv filename.
#EnumMatType=8  # dwp96 as well as tube96 seems to always be of material type 8.
#EnumSlotNr=%(slotnr)s  # SlotNr; robot specific; assigned by valet object
#Stapelindex=0  # The rack is not standing on top of anything.
#RackLevelSensor=0 # Disables liquid detection sensor for all wells.
#StartVolumenNanoliter_0=100000   - Is used to set volume of all wells to 100 ul.
# This is for DNAtechnology 96 tube plates:
#MatDatei=./top/dws/plates/tubes96/MICR_TP_1300_5
#MatName=MICR_TP_1300_5
#EnumMatType=8
#ReagenzName_0=Tubes96_Pos1
#StartVolumenNanoliter_0=111000

            "cmd-placeit-tips":"""
[%(cmdindex)03d]
OpcodeStr=Place it
Opcode=115
MatDatei=./top/dws/tips/tip50f
MatName=tip50f
BehaelterName=tips%(cmdindex)03d
EnumMatType=4
EnumSlotNr=%(slotnr)s
""",
            "method-prefix":"""
[Properties]
Comment=Produced by Staplemixer script
DWS-ability=0x0000FF06
Name=%(filename)s

[Version]
Name=%(filename)s
Struktur=PrgStruc 0.21

[001]
OpcodeStr=Place it
Opcode=115
MatDatei=./top/dws/trth/Rack_1_5ml
MatName=Rack_1_5ml
BehaelterName=%(destin-rackname)s
EnumMatType=512
EnumSlotNr=160
Stapelindex=0
RackLevelSensor=0
%(dest-pos-names)s
""",
# Old: used to use ReagenzNamen=Name1|Name2|Name2, etc. But this seems to have changed.
#MatDatei=./top/dws/trth/Rack_1_5ml_SAR
#MatName=Rack_1_5ml_SAR
# Yes, [001] PlaceIt cmd is allocated for placing dest-rack.
# This is hardcoded in the second part of generateRobotFile.
# If you want to change, you must re-code and re-test.
            "cmds-after-placeit":["""
[%(cmdindex)03d]
OpcodeStr=Comment
Opcode=113
Bezeichner=Starting Staples->Modules pipetting.
""","""
[%(cmdindex)03d]
OpcodeStr=Thermomixer
Opcode=123
Bezeichner=Place a container with water on the thermomixer. I will heat it, in order to increase the humidity in the hood.
WithTemplate=0
SpeedOn=0
MixSpeed=500
MixTimeMinute=1
MixTimeSecond=0
TempOn=1
Temperature=60
TempHold=1
""","""
[%(cmdindex)03d]
OpcodeStr=UserIntervention
Opcode=114
Bezeichner=Init completed, ready to start pipetting. ----> 1) PLEASE CHECK THAT ALL RACKS ARE PROPERLY ORIENTED !! <----- 2) You should also PLACE A BEAKER with MilliQ water on the heated THERMOMIXER in order to increase humidity in the robot workspace hood.
Alarm=1
""",
"""
[%(cmdindex)03d]
OpcodeStr=NumberOfSamples
Opcode=118
Fest=1
festeProbenzahl=1
maxProbenzahl=0
"""],
            "method-postcmds":[
"""
[%(cmdindex)03d]
OpcodeStr=Thermomixer
Opcode=123
Bezeichner=Re-set thermomixer, otherwise the temperature will be on even after the method is complete.
WithTemplate=0
SpeedOn=0
MixSpeed=500
MixTimeMinute=1
MixTimeSecond=0
TempOn=1
Temperature=50
TempHold=0

""","""
[%(cmdindex)03d]
Bezeichner=
OpcodeStr=PostRun
Opcode=117

""","""
[%(cmdindex)03d]
OpcodeStr=End
Opcode=129

"""     ],
            "cmd-template":"""
[%(cmdindex)03d]
Opcode=101
OpcodeStr=SampleTransfer
Source1=%(source-rackname)s
Source_Pat_Z1=%(source-row)s
Source_Pat_S1=%(source-col)s
Source_Pat_T1=1
Destination1=%(destin-rackname)s
Destination_Pat_Z1=%(destin-row)s
Destination_Pat_S1=%(destin-col)s
Destination_Pat_T1=1
TransferVolumenNanoliter=%(transfer-vol-nl)s
Filter=1
LiqName=Water
Bezeichner=%(cmd-comment)s
ToolName=TS_50
ToolDatei=./top/dws/tools/TS_50
LiqDatei=./top/dws/liquids/Water
SrcSimple=1
MixBefore=1
MixBeforeTumSpeed=7500
MixBeforeVolumenNanoliter=15000
MixBeforeNoOfCycles=3
MixBeforeFixedHeight=1
MixBeforeFixAb=4000
MixBeforeFixAuf=2000
Source_Pat_AnzDup=1
Source_Pat_Vorhanden=1
Destination_Pat_AnzDup=1
Destination_Pat_Vorhanden=1
"""             #End cmd-template
            } # End robot config
        } # End config


# ROW in German is Zeile
# Column in German is Saule
# epMotion index starts at 1, i.e. A1 is Z=1, S=1; A2 <=> Z=1, S=2, etc.

# EpMotion layout (mapping pos to EnumSlotNr)
#    TOOLS   A2      A3     TMX
#    B1      B2      B3
#    C1      C2      C3
#
#    TOOLS   151     152    153
#    156     155     154
#    160     161     162

# Unknown: 151, 152, 156,

    def getConfig(self):
        return self.Config

    def getCmdTemplates(self):
        return self.Config["robot"]

    def safeConfig(self, config=None, filename=None, format="yaml"):
        # Just realized how shitty JSON is for storing configs: NO LINE BREAKS...
        format = format.lower()
        if not format in ("yaml", "json"):
            print "Format: " + string(format) + " is not supported. Falling back to yaml."
            format = "yaml"
        if config is None:
            config = self.Config
        if str(config) == "robot":
            config = self.Config["robot"]
            if filename is None:
                filename = "staplemixer-robot.cfg"
        if filename is None:
            filename = "staplemixer.cfg"

        if format == "yaml":
            self.saveYaml(config, filename)
        elif format == "json":
            self.saveJson(config, filename)
        else:
            print "WHAT"

    def saveJson(self, config, filename):
        with open(filename, 'wb') as cfgfile:
            #cfgfile.write(json.dumps(config))
            json.dump(config, cfgfile)

    def saveYaml(self, config, filename):
        with open(filename, 'wb') as cfgfile:
            yaml.dump(config, cfgfile, default_flow_style=False, default_style="|")

    # Remember to use safe_load !
    def loadYaml(self, filename):
        with open(filename, 'rU') as cfgfile:
            config = json.safe_load(cfgfile)
        return config

    # Seriously, just use json.load(open(filename,'rU')) instead.?
    def loadJson(self, filename):
        with open(filename, 'rU') as cfgfile:
            config = json.load(cfgfile)
        return config






#[002]
#OpcodeStr=Place it
#Opcode=115
#MatDatei=./top/dws/plates/dwp96/AB_DWP_1200
#MatName=AB_DWP_1200
#BehaelterName=(sourcerack)s
#EnumMatType=8
#EnumSlotNr=161

#[003]
#OpcodeStr=Place it
#Opcode=115
#MatDatei=./top/dws/plates/dwp96/AB_DWP_1200
#MatName=AB_DWP_1200
#BehaelterName=(rack2)s
#EnumMatType=8
#EnumSlotNr=162

#[004]
#OpcodeStr=Place it
#Opcode=115
#MatDatei=./top/dws/plates/dwp96/AB_DWP_1200
#MatName=AB_DWP_1200
#BehaelterName=(rack3)s
#EnumMatType=8
#EnumSlotNr=154

#[005]
#OpcodeStr=Place it
#Opcode=115
#MatDatei=./top/dws/tips/tip50f
#MatName=tip50f
#BehaelterName=tips1
#EnumMatType=4
#EnumSlotNr=151

#[006]
#OpcodeStr=Place it
#Opcode=115
#MatDatei=./top/dws/tips/tip50f
#MatName=tip50f
#BehaelterName=tips2
#EnumMatType=4
#EnumSlotNr=152

#""",
##[007]
##OpcodeStr=Comment
##Opcode=113
##Bezeichner=Starting Staples->Modules pipetting.

##[008]
##OpcodeStr=NumberOfSamples
##Opcode=118
##Fest=1
##festeProbenzahl=1
##maxProbenzahl=0


if __name__ == "__main__":
    cg = ConfigGenerator()
    cg.safeConfig()
    cg.safeConfig("robot")

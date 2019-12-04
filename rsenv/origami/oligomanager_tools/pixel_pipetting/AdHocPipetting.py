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
Created on Thu Jun 16 11:08:43 2011

@author: scholer
"""

import csv

## Based on PixelPipetting.py


class Helper:

    def getRowFromPos(self, pos):
        if not pos:
            print("EpMotion:getRowFromPos(): Unexpected event: No pos...")
            return None
        return ord(pos[0].lower()) - ord('a') + 1
    def getColFromPos(self, pos):
        if not pos:
            print("EpMotion:getColFromPos(): Unexpected event: No pos...")
            return None
        return int(pos[1:])


    def __init__(self):


        # Z = row, S = saule = column
        # Source_Pat_Z1=3 # C
        # Source_Pat_S1=8 # 8
        self.STcmd = """
[%(cmdnum)03d]
Opcode=101
OpcodeStr=SampleTransfer
Source1=%(srcrack)s
Source_Pat_Z1=%(srcrowindex)d
Source_Pat_S1=%(srccolindex)d
Source_Pat_T1=1
Destination1=PixelRack
Destination_Pat_Z1=%(dstrowindex)d
Destination_Pat_S1=%(dstcolindex)d
Destination_Pat_T1=1
TransferVolumenNanoliter=10000.0
Filter=1
LiqName=Water
Bezeichner=
ToolName=TS_50
ToolDatei=./top/dws/tools/TS_50
LiqDatei=./top/dws/liquids/Water
SrcSimple=0
Source_Pat_AnzDup=1
Source_Pat_Vorhanden=1
Destination_Pat_AnzDup=1
Destination_Pat_Vorhanden=1
MixBefore=1
MixBeforeTumSpeed=7500
MixBeforeVolumenNanoliter=15000
MixBeforeVolumenUnit=0
MixBeforeNoOfCycles=2
MixBeforeFixedHeight=1
MixBeforeFixAb=1000
MixBeforeFixAuf=2500
"""
#MixBefore=1
#MixBeforeTumSpeed=7500
#MixBeforeVolumenNanoliter=40000
#MixBeforeVolumenUnit=0
#MixBeforeNoOfCycles=2
#MixBeforeFixedHeight=0
#MixBeforeFixAb=0
#MixBeforeFixAuf=0
##MixAfter=1 # "Mix after dispensing" check-mark
##MixAfterTumSpeed=7500 # = 7.5 mm/sec
##MixAfterVolumenNanoliter=40000  # 40 ul
##MixAfterVolumenUnit=0
##MixAfterNoOfCycles=2
##MixAfterFixedHeight=0 # Fixed height (check-mark)
##MixAfterFixAb=0 # Fixed height aspirating (in um)
##MixAfterFixAuf=0 # Fixed height when dispensing (in um)
##MixBefore=0

        self.InitCmdCount = 10 # The last cmd number in InitStr.

        self.InitStr = """
[Properties]
Name=PixelPipettingDWS
Comment=
DWS-ability=0x0000FF06

[Version]
Name=pp_20110617-1208.dws
Struktur=PrgStruc 0.21


[001]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/tips/tip50f
MatName=tip50f
BehaelterName=tip50f_3
EnumMatType=4
EnumSlotNr=153
Stapelindex=0
RackTemperatur=0

[002]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/tips/tip50f
MatName=tip50f
BehaelterName=tip50f_2
EnumMatType=4
EnumSlotNr=156
Stapelindex=0
RackTemperatur=0

[003]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/tips/tip50f
MatName=tip50f
BehaelterName=tip50f_1
EnumMatType=4
EnumSlotNr=151

[004]
OpcodeStr=Place it
Opcode=115
MatDatei=./top/dws/trth/Rack_1_5ml_SAR
MatName=Rack_1_5ml_SAR
BehaelterName=PixelRack
EnumMatType=512
EnumSlotNr=152


[005]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
MatName=AXYG_DWP_600
EnumMatType=8
BehaelterName=Finv_and_Ico
EnumSlotNr=162

[006]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
MatName=AXYG_DWP_600
EnumMatType=8
BehaelterName=TR.SS.Jan2011_97-193
EnumSlotNr=161

[007]
OpcodeStr=Place it
Opcode=115
Bezeichner=
MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
MatName=AXYG_DWP_600
EnumMatType=8
BehaelterName=TR.SS.Jan2011_1-96
EnumSlotNr=160

[008]
OpcodeStr=PreRun
Opcode=116
Bezeichner=

[009]
OpcodeStr=Comment
Opcode=113
Bezeichner=Starting pixel pipetting.

[010]
OpcodeStr=NumberOfSamples
Opcode=118
Bezeichner=
Fest=1
festeProbenzahl=1
maxProbenzahl=0
"""

        self.PostRunCmd="""
[%03d]
Bezeichner=
OpcodeStr=PostRun
Opcode=117
"""
        self.EndCmd="""
[%03d]
OpcodeStr=End
Opcode=129
"""

if __name__ == "__main__":

    # Input file must be formatted in rows containing (dest-row	src-rack	src-pos)
    h = Helper()
    csvreader =  csv.reader(open('IcoKyle.csv', 'rU'), delimiter='\t')

    print(h.InitStr)
    i = h.InitCmdCount

    for row in csvreader:
        #print "dealing with row: " + ", ".join(row)
        if not row:
            #print "row does not contain any info..."
            continue
        if (row[0] == 'pixelpos' or 'Pos' in row):
            #print "row contains 'Pos'"
            continue
        i += 1
        # row is a list of the (column) entries in the file's line.
        print(h.STcmd % dict(cmdnum=i,
                             srcrack=row[1],
                             srcrowindex=h.getRowFromPos(row[2]),
                             srccolindex=h.getColFromPos(row[2]),
                             dstrowindex=h.getRowFromPos(row[0]),
                             dstcolindex=h.getColFromPos(row[0]),
                             ))

    i += 1
    print(h.PostRunCmd % i)
    i += 1
    print(h.EndCmd % i)



## Old InitStr:

##        self.InitStr = """
##[Properties]
##Comment=
##DWS-ability=0x0000FF06
##Name=PixelPipettingDWS
##
##[Version]
##Name=pixelpipetting.dws
##Struktur=PrgStruc 0.21
##
##[001]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
##MatName=AXYG_DWP_600
##BehaelterName=PixelRack
##EnumMatType=8
##EnumSlotNr=152
##
##[002]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
##MatName=AXYG_DWP_600
##BehaelterName=TR.SS.Jan2011_194-
##EnumMatType=8
##EnumSlotNr=162
##
##[003]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
##MatName=AXYG_DWP_600
##BehaelterName=TR.SS.Jan2011_97-193
##EnumMatType=8
##EnumSlotNr=161
##
##[004]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/plates/dwp96/AXYG_DWP_600
##MatName=AXYG_DWP_600
##BehaelterName=TR.SS.Jan2011_1-96
##EnumMatType=8
##EnumSlotNr=160
##
##[005]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/tips/tip50
##MatName=tip50
##BehaelterName=tips1
##EnumMatType=4
##EnumSlotNr=151
##
##[006]
##OpcodeStr=Place it
##Opcode=115
##MatDatei=./top/dws/tips/tip50
##MatName=tip50
##BehaelterName=tips2
##EnumMatType=4
##EnumSlotNr=156
##
##[007]
##OpcodeStr=Comment
##Opcode=113
##Bezeichner=Starting ad-hoc pipetting.
##
##[008]
##OpcodeStr=NumberOfSamples
##Opcode=118
##Fest=1
##festeProbenzahl=1
##maxProbenzahl=0
##"""

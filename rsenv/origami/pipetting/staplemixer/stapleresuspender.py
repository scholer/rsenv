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
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.



from .staplemixer import StapleMixer


class StapleResuspender(StapleMixer):
    """
    Uh, just FYI: I morges da jeg stod op syntes jeg lige pludselig det var en super dårlig
    idé at gøre dette her: Det er jo meget hurtigere bare at programmere robotten manuelt
    da mønstret er simpelt: flyt fra 1 destination til hele pladen, evt ved at bruge
    bruge 8-channel pipette, eller single-channel for den sags skyld.
    MEN: Jeg skal jo have forskelligt volumen for hver brønd! Uh, det gør det lige pludselig
    ret besværligt; hver kommando kan kun have ét volumen, så skal jeg have 96 forskellige cmds
    for hver plade.
    DERFOR: Dette script er alligevel en god idé.

    Implementations:
    a) Just use standard TS_300 tool.
    b) Optimized: Pipet as much as possible with eight-channel TS_300_8 and the rest with single channel
       NO:: 8-channel requires the same volume for all wells in the same column; If this were the
       requirement, it would be easier to simply programme the robot manually.

    Function:
    1) Read rackfiles (inherited from staplemixer)
    2) Generate pipet data
        This is maybe not needed?
        On the other hand, if I just generate this, I can use the generateRobotFile inherited from StapleMixer
    3) Generate robot dws from pipet data
        Yes, use the inherited generateRobotFile() method.
        Except, that uses dest-index, not Pos for destination :-\
        However, I don't _have_ to use that. I can just define a new PipDataFields header.
        The only thing that counts is that the rowdict (from pipetdataset) is sent through
        pipetinstructionToCmdVars(), which generates destin-row,destin-col from destin-index.

    Concrete:
    - for plate in rackdata
    -
    Edit: This is currently implemented directly into the main staplemixer script.
    """

    # def generateResuspendInstructions(self):
    #
    #
    #     for rack in self.Rackdata:
    #
    #         # old:
    #         pipetdataset.append(dict(zip(
    #         self.PipDataFields, #["row","source-rackname","source-pos","destin-rackname","destin-index","volume","comment"]
    #         [pipetrow, rackrow["rackname"], sourcepos, destrackname, str(destindex), str(volume),
    #             "".join([modulename,": ", rackrow["rackname"],":",sourcepos,"->",destrackname,":",str(destindex)])
    #         ])))
    #
    #
    #         # New
    #         self.PipDataFields = ["row","source-rackname","source-pos","destin-rackname","destin-pos","volume","comment"]
    #         sourcepos=rackrow[self.findFieldByHint(rackrow.keys(), "pos")]
    #         pipetdataset.append(dict(zip(
    #         self.PipDataFields,
    #         #["row","source-rackname","source-pos","destin-rackname","destin-index","volume","comment"]
    #         [pipetrow, "BufferTub", "A01", rackrow["rackname"], sourcepos, destrackname, str(destindex), str(volume),
    #             "{}: {}:{}->{}:{}".format(modulename,rackrow["rackname"],sourcepos,destrackname,destindex)
    #         ])))

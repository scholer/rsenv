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
# pylint: disable-msg=R0903
# R0903: Too few public methods.


class EpmotionValet(object):
    """
    This class is used to park labware in the robot, keeping track of
    which slots are used.
        # EpMotion layout, positions names:
        #   T0  T1..4     A2      A3     TMX
        #   B0    B1      B2      B3     VAC
        #  TRASH  C1      C2      C3     C4
        #
        # EpMotion layout, mapped to EnumSlotNr: (Edited Feb 2013 and it is like THIS:)
        #      TOOLS     151     152    157
        #  155   156     153     154    158
        #        160     161     162    159
    It is secondarily used to store and retrieve information about epmotion labware.
    (In the future, available labware information will be persisted as a yaml file and
    not hard-coded in source...)

    Attributes:
     -  Slots: Keeps track of which slots are available/occupied.
        Dict with slot=True/False key-value pairs, where False=Empty and True=Occupied.

     -  Favs: Dict of type=[list of favorite slots for that type]. Used to select different
        slots preferentially for different types of equipment.

    Methods:
    -   valet(mattype) : Used to park a piece of labware in the robot.

    """
    def __init__(self):
        slots = [151, 152, 153, 154, 155, 156, 160, 161, 162]
        self.Slots = dict(zip(slots, [False]*len(slots))) # True = occupied
        self.Favs = dict(   sourcerack = [161, 162, 154, 153, 156],
                            destrack = [160],
                            tips = [153, 156, 154, 151, 152],
                            tub = [154, 152, 162]
                        )
        self.ToolData = dict(TS_50  ="./top/dws/tools/TS_50",
                             TS_300 ="./top/dws/tools/TS_300",
                             TS_1000="./top/dws/tools/TS_1000")
    """
    Park/position a piece of labware, based on what material type it is).
    """
    def valet(self, mattype):
        """
        Place/park a piece of labware/mattype in the best position available.
        The slot is then marked as occupied.
        """
        for favslot in self.Favs[mattype]:
            if not self.Slots[favslot]:
                self.Slots[favslot] = True
                return favslot
        print "Valet: Could not find slot for type: " + mattype
        return None



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

## SUT:
from staplemixer.epmotionvalet import EpmotionValet


def test_epmotionvalet_basic():
    valet = EpmotionValet()
    occ = list()
    valet.valet('sourcerack')
    occ.append(161)
    assert all(occupied if key in occ else not occupied for key, occupied in valet.Slots.items() )
    valet.valet('destrack')
    occ.append(160)
    assert all(occupied if key in occ else not occupied for key, occupied in valet.Slots.items() )
    valet.valet('tub')
    occ.append(154)
    assert all(occupied if key in occ else not occupied for key, occupied in valet.Slots.items() )
    valet.valet('tips')
    occ.append(153)
    assert all(occupied if key in occ else not occupied for key, occupied in valet.Slots.items() )

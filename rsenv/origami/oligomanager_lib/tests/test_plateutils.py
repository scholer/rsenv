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




from rsenv.origami.oligomanager_lib.oligodatalib.plateutils import *



def test_posToRowColTup():
    pos_assertions = dict(A01=(1,1), A02=(1,2), A07=(1,7), B01=(2,1), B04=(2,4), D12=(4,12) )
    for pos, tup in pos_assertions.items():
        assert posToRowColTup(pos) == tup


def test_indexToRowColTup():
    # index, ncols=12, nrowmax=8):
    index_assertions = { 0:(1,1), 1:(1,2), 2:(1,3), 11:(1,12), 12:(2,1), 23:(2,12), 24:(3,1) }
    for idx, tup in index_assertions.items():
        assert indexToRowColTup(idx) == tup

def test_indexToPos():
    # index, ncols=12, nrowmax=8):
    index_assertions = dict( A01=0, A02=1, A12=11, B01=12, B12=23, C01=24 )
    for pos, idx in index_assertions.items():
        assert indexToPos(idx) == pos

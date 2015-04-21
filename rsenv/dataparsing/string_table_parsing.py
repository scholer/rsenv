#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2014 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

Module for parsing text (e.g. from copy/pasted from clipboard).


"""

from tabulated_data import tabdata_as_dictlist
from textdata_util import gen_trimmed_lines

def strtable_to_dictlist(strtable, headers=None, sep=None, stripcells=True):
    """
    Returns a list of dicts based on strtable input.
    """
    tabdata = gen_trimmed_lines(strtable.split('\n'))
    return tabdata_as_dictlist(tabdata, headers=headers, sep=sep, stripcells=stripcells)



if __name__ == '__main__':
    # This is the table you get when you analyze a sequence vs restriction endonucleases:
    inputtable = """

Name	Sequence	Site Length	Overhang	Frequency	Cut Positions

AccI	GTMKAC	6	five_prime	6	378, 620, 880, 965, 1222, 1345
# This is a comment!
AciI	CCGC	4	five_prime	28	37, 59, 112, 143, 177, 188, 263, 312, 324, 401, 415, 541, 589, 663, 718, 748, 793, 937, 985, 1026, 1030, 1061, 1125, 1201, 1461, 1473, 1477, 1506
AflIII	ACRYGT	6	five_prime	1	597
AluI	AGCT	4	blunt	1	1017
# End of document

"""
    dictlist = strtable_to_dictlist(inputtable)
    row = dictlist[0]
    assert set(row.keys()) == set("Name	Sequence	Site Length	Overhang	Frequency	Cut Positions".split('\t'))
    assert row['Name'] == 'AccI'
    assert row['Sequence'] == 'GTMKAC'
    assert row['Site Length'] == '6'
    assert row['Overhang'] == 'five_prime'
    assert row['Frequency'] == '6'
    assert row['Cut Positions'] == '378, 620, 880, 965, 1222, 1345'
    row = dictlist[-1]
    assert row['Name'] == 'AluI'
    assert row['Sequence'] == 'AGCT'
    assert row['Site Length'] == '4'
    assert row['Overhang'] == 'blunt'
    assert row['Frequency'] == '1'
    assert row['Cut Positions'] == '1017'
    print "ALL OK!"

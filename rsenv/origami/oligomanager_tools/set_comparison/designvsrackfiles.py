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
Created on Mon Aug  8 15:03:52 2011

@author: scholer
"""


from compareoligosets import *


if __name__ == "__main__":
    import argparse
    # # The script is module-aware, meaning it will first sort the oligos by module (or color!) and then examine the difference between the modules.')
    argparser = argparse.ArgumentParser(description='This script is used to compare the oligo-set in a origami design against the oligos found in rackfiles.') 
    argparser.add_argument('designfilename', help="Compare this oligo-list against the rackfiles." )
    argparser.add_argument('rackfiles', nargs='*', help="List of rackfiles in csv format. If not provided, program will glob for *.rack.csv files." )
    args = argparser.parse_args()
    
    compareDesignVsRackfiles(args.designfilename, None)

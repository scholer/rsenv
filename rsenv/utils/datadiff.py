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
# pylint: disable-msg=C0103,C0301,R0913
# R0913: Too many function arguments.

"""
Copyright 2014 Rasmus Scholer Sorensen, rasmusscholer@gmail.com

@author: scholer

Instead of rolling your own datadiff code, use existing modules, e.g. the datadiff module:
 - https://pypi.python.org/pypi/datadiff
Alternatively, see:
 - http://stackoverflow.com/questions/1165352/fast-comparison-between-two-python-dictionary
 - http://stackoverflow.com/questions/6632244/difference-in-a-dict

"""

try:
    from . import datadiff
except ImportError:
    datadiff = None


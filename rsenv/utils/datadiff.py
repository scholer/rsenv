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


Alternative or similar packages (active projects):

* https://pypi.org/project/diff/,
    * https://github.com/Julian/Diff
* https://pypi.org/project/simple-diff/
    * https://github.com/alvinchchen/simple_diff
    * Very basic.
* https://pypi.org/project/nested-diff/
    * https://github.com/mr-mixas/Nested-Diff.py
* https://pypi.org/project/deep-diff/
    * https://github.com/ider-zh/diff
* https://pypi.org/project/recursive-diff/
    * https://github.com/crusaderky/recursive_diff
* https://pypi.org/project/difftrack/
    * https://github.com/qntln/difftrack
    * Track changes in data structures and create listeners.


Inactive projects:

* https://pypi.org/project/datadiff/
    * https://sourceforge.net/projects/datadiff/
    * Last release 2015.
* https://pypi.org/project/diff-tools/
    * https://github.com/mcai4gl2/diff-tools
* https://pypi.org/project/diff_py/
    * https://github.com/askeing/diff_py


Diff on structured text:

* https://pypi.org/project/csv-diff/
    * https://github.com/simonw/csv-diff
    * Provides `csv-diff` CLI,
* https://pypi.org/project/json-diff/
    * https://gitlab.com/mcepl/json_diff
    * Provides `json_diff` CLI for diffing json files.
    * Weirdly enough, the PyPI project is called `json-diff`, but the CLI is called `json_diff`.
* https://pypi.org/project/html-diff-wrapper/


Other diff packages:

* https://pypi.org/project/unidiff/
    * Package to operate on data in the "unified diff" text file format.


"""

try:
    from . import datadiff
except ImportError:
    datadiff = None


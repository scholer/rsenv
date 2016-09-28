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
"""
Contains various file-level functions,
e.g. batch rename, etc.
"""

from __future__ import print_function, absolute_import
import os
import glob
from builtins import input  # works on python 2 and 3


def listcwddirs(cwdpath=None, returnasabspath=False):
    """
    Returns directories in current directory. Mostly for reference.
    """
    if cwdpath is None:
        cwdpath = os.getcwd()
    if returnasabspath:
        path = os.path.abspath
    else:
        path = lambda d: d
    return [path(d) for d in os.listdir(cwdpath) if os.path.isdir(os.path.abspath(d))]


def search_replace_file_rename(rootdir, find_str, replace_str, prompt=True, verbose=True):
    """
    Recursively rename all files and directories starting from (but not including) rootdir.
    With prompt=True, the function will ask for all renames (default).
    Returns a list of (oldpath, newpath) tuples containing all rename actions performed.

    Usage:
    >>> rename_files('.', 'RS311i', 'RS316j')
    [
        ('.\\RS311i PAGE of SubP-staples samples v2', '.\\RS316j PAGE of SubP-staples samples v2'),
        ('.\\RS316j PAGE of SubP-staples samples v2\\RS311i_SubP-Staples_PAGE_20140827_500V-0-40k.png',
         '.\\RS316j PAGE of SubP-staples samples v2\\RS316j_SubP-Staples_PAGE_20140827_500V-0-40k.png'),
        (...)
    ]
    """
    choice = '' if prompt else 'Y'
    rename_tups = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        for i, element in enumerate(dirnames+filenames):
            if find_str in element:
                newfn = element.replace(find_str, replace_str)
                oldpath = os.path.join(dirpath, element)
                newpath = os.path.join(dirpath, newfn)
                if newfn in dirnames+filenames:
                    print("Cannot rename %s to %s because %s is already in %s, continuing..."
                          % (oldpath, newpath, newfn, dirpath))
                    continue
                if not choice or (choice and choice[0] not in 'YN'):
                    choice = input(
                        ("Rename file '%s' to '%s' ? [ y=yes for this file, Y=Yes for all, "
                         "n=no--not for this file, N=No--abort ]\n") % (oldpath, newpath))
                if choice:
                    if choice[0] == 'N':
                        break
                    if choice[0] in 'yY':
                        os.rename(oldpath, newpath)
                        rename_tups.append((oldpath, newpath))
                        # Altering dirnames list in place should be ok, right?
                        if element in dirnames and dirnames[i] == element:
                            dirnames[i] = newfn
                        if verbose:
                            print("+ Renamed '%s' to '%s'" % (oldpath, newpath))
    return rename_tups

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

This module is intended as much as a reference as an actual functional
tools list, so you can look up conversions when you cannot remember them.

"""

from constants import *

wavenumber_to_energy(wavenumber):
    """
    Converts wavenumber (in reciprocal cm) to energy in Joule.
    Wavenumber is defined as 1/wavelength, also written as
    <nu> = 1/<lambda>
    http://en.wikipedia.org/wiki/Wavenumber
    """
    E = h*c*wavenumber # Probably needs unit conversion?

wavenumber_to_wavelength(wavenumber):
    """
    Converts wavenumber (in reciprocal cm) to wavelength in nm.
    Wavenumber is defined as 1/wavelength, also written as
    <nu> = 1/<lambda>.
    Since wavenumber is (1/cm) and wavelength is nm, we
    return 1/wavenumber * 1e7.
    http://en.wikipedia.org/wiki/Wavenumber
    """
    nm = 1e7/wavenumber
    return nm
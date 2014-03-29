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


import math

try:
    from scipy.constants import *
except ImportError:
    ## From scipy source code at github:
    pi = math.pi
    c = 299792458
    mu_0 = 4e-7*pi
    epsilon_0 = 1 / (mu_0*c*c)
    h = 6.62606957e-34
    hbar = h / (2 * pi)
    R = 8.314472
    N_A = Avogadro = 6.02214129e23 # Avogadro constant
    k = Boltzmann = 1.3806504e-23  # Boltzmann constant
    e = elementary_charge = 1.602176487e-19 # elementary charge


    # SI prefixes
    yotta = 1e24
    zetta = 1e21
    exa = 1e18
    peta = 1e15
    tera = 1e12
    giga = 1e9
    mega = 1e6
    kilo = 1e3
    hecto = 1e2
    deka = 1e1
    deci = 1e-1
    centi = 1e-2
    milli = 1e-3
    micro = 1e-6
    nano = 1e-9
    pico = 1e-12
    femto = 1e-15
    atto = 1e-18
    zepto = 1e-21

    # binary prefixes
    kibi = 2**10
    mebi = 2**20
    gibi = 2**30
    tebi = 2**40
    pebi = 2**50
    exbi = 2**60
    zebi = 2**70
    yobi = 2**80

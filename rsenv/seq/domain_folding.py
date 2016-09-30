#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2016 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#


"""

Module for generating oligo sequences by folding domains onto each other.

Examples:
    generate_fbsplint(seq_to_circularize) will generate a "fb-splint" with domains annealing not
    only to the ends but also to the middle:
                             A          F
        .-----------------------5P 3---------------------.
        |               .--------------------.           |
        | B             |    A*         F*   |           |
        |               |   C*         D*    |        E  |
        |               `-------5P 3---------'           |
        `------------------------------------------------'
                            C          D

"""

from .sequtil import rcompl



def generate_fbsplint_seq(seq, domain_sizes=(10, 10, 11, 11), sep='-'):
    """Generate a "fb-splint"
    An fb-splint is a splint oligo with domains annealing not
    only to the ends but also to the middle:
                             A          F
        .-----------------------5P 3))))))))))-----------.
        |               .-----------–—–~-–––––           |
        | B             |    A*         F*   |           |
        |               |   C*         D*    |        E  |
        |               `--------5 3---------'           |
        `------------------------------------------------'
                            C          D

    This greatly increases the thermodynamic stability of the circular product
    relative to side-products (e.g. splinting two oligos together).
    Using fb splints, circularization of 5' phosphorylated oligos can be done in
    micro-molar concentrations, whereas if normal splints are used, the circularization
    must be done at nano-molar concentrations to prevent dimeric side-products.

    Args:
        seq_to_circularize: The sequence of the 5' phosphorylated oligo to circularize.
        domain_sizes: Sizes of domains in order (C*, A*, F*, D*).
        sep: Separator between domains
    Returns:
        sequence for fb-splint oligo.

    Based on: make_fb_splint() in RS398 Notebook.
    """
    # fp splint domains (on seq): mid-upstream, 5', 3', mid-downstream
    d1, d2, d3, d4 = domain_sizes
    mid = round(len(seq)/2)
    splint = sep.join(rcompl(d) for d in [seq[mid:mid+d1], seq[:d2], seq[-d3:], seq[mid-d4:mid]])
    print(splint, "\t", "-".join(str(len(part)) for part in splint.split("-")))
    return splint

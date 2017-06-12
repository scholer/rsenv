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

from math import floor, ceil
import numpy as np

from .sequtil import rcompl


def generate_fbsplint_seq(template, domain_sizes=(10, 10, 11, 11), mid=0.5, sep='-', check_lengths=True, debug=False):
    """Generate a "fb-splint"
    An fb-splint is a splint oligo with domains annealing not
    only to the ends but also to the middle:
                             A          F
        .-----------------------5P 3---------------------.
        |               .--------------------.           |
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
        template: The sequence of the 5' phosphorylated oligo to circularize.
        domain_sizes: Sizes of domains in splint's 5'->3' order (C*, A*, F*, D* in the diagram above).
        sep: Separator between domains when printing the generated splint sequence.
        check_lengths: If True (default), print a warning if the domain lengths looks weird.
        mid: Where domain 1 (C*) and 4 (D*) of the fb-splint hybridize to the template sequence.
            Specifically, the point on template where the ends of fb-splint meet and stack.
            It may be beneficial to select a point with high stacking energy, e.g. C/G basepair.
            Values can be fractional (<1) or absolute (>1).
            Default value of 0.5 means "at the middle/halfway".
    Returns:
        Sequence for fb-splint oligo.

    Based on: make_fb_splint() in RS398 Notebook.
    """
    # fp splint domains (on template): mid-upstream, 5', 3', mid-downstream
    accepted_helix_lengths = {20, 21, 32}
    l1, l2, l3, l4 = domain_sizes

    if check_lengths:
        if l1+l4 != l2+l3:
            print("WARNING: l1+l4 != l2+l3: (%s+%s) != (%s+%s" % (l1, l4, l2, l3))
        if l1+l4 not in accepted_helix_lengths:
            print("WARNING: l1+l4 (%s+%s) not in accepted helix lengths %s" % (l1, l4, accepted_helix_lengths))
    if mid < 1:
        mid = ceil(mid * len(template))
    # splint = sep.join(rcompl(d) for d in [template[mid:mid+l1], template[:l2], template[-l3:], template[mid-l4:mid]])
    # Template domains:
    A, B, C, D, E, F = [
        template[:l2], template[l2:mid - l1], template[mid - l1:mid],
        template[mid:mid + l4], template[mid + l4:-l3], template[-l3:]
    ]
    # Splint domains, joined by sep:
    splint = sep.join(rcompl(d) for d in (C, A, F, D))
    if debug:
        print(splint, "\t", "-".join(str(len(part)) for part in splint.split("-")))
    return splint


def printable_fb_splint_diagram(seq, splint=None, domain_sizes=(10, 10, 11, 11), mid=0.5,
                                stack_sep="-5 3-", blank="-", assert_seqs=True):
    """Print diagram with the fb-splint folded domains:

                     A              F
        AGAGCCCAATGCGAAGTA-5 3-GTAAATCCTCAATCAAT.
        |       TACGCTTCAT-----CATTTAGGAGT      |
        |B      |    a              f    |      |
        |       |    c              d    |     E|
        |       GAGAACCTGA-5 3-GATTGATGAGA      |
        `ACGAGGACTCTTGGACT-----CTAACTACTCTCACACTC
                     C              D

    :param seq: oligo sequence to be circularized
    :param splint: splint sequence
    :param domain_sizes: domain_sizes parameter for generate_fbsplint_seq.
    :param mid: The ```mid``` parameter for generate_fbsplint_seq
    :param stack_sep: The "stacking" part of the diagram.
    :param blank: The padding character to use when no base is
        present but we need a placeholder character for alignment.
    :return: String representation of the fb-splint folded domain diagram.

    Examples:
        print(printable_fb_splint_diagram("ATGAAGCGTAACCCGAGAACGAGGACTCTTGGACTCTAACTACTCTCACACTCTAACTAACTCCTAAATG"))

    Notes:
        This was originally implemented using numpy.chararray, which allows you to do e.g.
            lines[:] = " "  and  lines[2:5, -1] = np.array(list('|||')), i.e. "vertical writing".
        But, since this use-case is mostly horizontal writing and only lille vertical writing,
        it could almost as easily be done with list-of-lists structure.
    """
    if mid < 1:
        mid = ceil(mid * len(seq))
    if domain_sizes is None:
        assert splint is not None
        c, a, f, d = splint.split("-")
        domain_sizes = [(len(d) for d in (c, a, f, d))]
    if splint is None:
        splint = generate_fbsplint_seq(seq, domain_sizes=domain_sizes, mid=mid, sep="")

    l1, l2, l3, l4 = domain_sizes
    c, a, f, d = splint[:l1], splint[l1:l1+l2], splint[l1+l2:l1+l2+l3], splint[l1+l2+l3:]
    A, B, C, D, E, F = [seq[:l2], seq[l2:mid-l1], seq[mid-l1:mid], seq[mid:mid+l4], seq[mid+l4:-l3], seq[-l3:]]
    if assert_seqs:
        try:
            assert all(len(s) == l for s, l in zip((c, a, f, d), domain_sizes))
            assert all(len(d) == len(D) for d, D in zip((c, a, f, d), (C, A, F, D)))
            assert all(rcompl(d) == D for d, D in zip((c, a, f, d), (C, A, F, D)))
        except AssertionError:
            print("ERROR")
            print("\n".join(
                " ".join(map(str, (rcompl(d) == D, d, D)))
                for d, D in zip((c, a, f, d), (C, A, F, D))))
            raise

    # Sub-domain sequences:
    B1, B2 = B[:ceil(len(B)/2)], B[ceil(len(B)/2):]
    E1, E2 = E[:ceil(len(E)/2)], E[ceil(len(E)/2):]
    B2 = "{:->{}}".format(B2, len(B1))  # Or use `, ', and . as corners?
    E2 = "{:->{}}".format(E2, len(E1))  # It will be reversed later
    line_width = (len(B1) + len(A) + len(stack_sep) + len(F) + len(E2))
    lines = [list(" "*line_width) for _ in range(8)]

    # Annotations and crossovers:
    for lno in range(2, 6):
        lines[lno][0] = "|"
        lines[lno][-1] = "|"
    for lno in range(3, 5):
        lines[lno][len(B1)] = "|"
        lines[lno][-len(E1)-1] = "|"
    annotations = {
        "A": (0, len(B1)+floor(len(A)/2)),
        "A*": (3, len(B1)+floor(len(A)/2)),
        "C*": (4, len(B1)+floor(len(A)/2)),
        "C": (7, len(B1)+floor(len(A)/2)),
        "F": (0, len(B1)+len(A)+len(stack_sep)+floor(len(F)/2)),
        "F*": (3, len(B1)+len(A)+len(stack_sep)+floor(len(F)/2)),
        "D*": (4, len(B1)+len(A)+len(stack_sep)+floor(len(F)/2)),
        "D": (7, len(B1)+len(A)+len(stack_sep)+floor(len(F)/2)),
        "B": (3, 1),
        "E": (4, -2),
    }
    for k, (row, col) in annotations.items():
        lines[row][col:col+len(k)] = k

    # thread oligo sequence:
    lines[1][:] = B1[::-1] + A[::-1] + stack_sep + F[::-1] + E2[::-1]
    lines[6][:] = B2 + C + len(stack_sep)*blank + D + E1

    # thread splint sequence:
    lines[2][:] = "|" + " "*(len(B1)-1) + a + blank*len(stack_sep) + f + " "*(len(E2)-1) + "|"
    lines[5][:] = "|" + " "*(len(B2)-1) + c[::-1] + stack_sep + d[::-1] + " "*(len(E2)-1) + "|"

    return "\n".join("".join(row) for row in lines)




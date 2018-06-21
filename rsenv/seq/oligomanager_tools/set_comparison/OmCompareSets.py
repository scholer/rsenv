#!/usr/bin/python

# Compare two oligo-design-sets:
# From csv-files, using columns from header seqence_mod
# TIP: os.getcwd() - current working directory...
# TODO: Create graphical user interface for this functionality.

"""

Old module which uses OmSetReader to read designsets from cadnano stapleseq csv export files,
and then OmToolbox.printSetDiffWithStringCompare() to compare the sets.

Has largely been superseeded by compareoligosets.py module.

"""

import os
import sys
from OmToolbox import OmToolbox
from OmSetReader import OmSetReader



if __name__ == '__main__':
    # sys.argv is a list where the first element is the name of the invoked script (command-line), the rest is the arguments passed.
    designs = list()
    print sys.argv
    for filepath in sys.argv[1:]:
        # OmSetReader init takes filepath, mismap file, csv delimitor.
        designs.append(OmSetReader(filepath, 'allT')) # Basically just insert 'T' instead of '?'.

    print "Start script..."
    cwd = os.getcwd()
    print "Working directory: %s" % cwd

    tbx = OmToolbox()

    # designs.oligoset contains the set of oligos used in that design.
    # designs.seqdict contains the rest of the information in the set-list file (e.g. Color, Start, End, etc).
    # This seqdict is indexed using the sequence which makes it easy to find info for a particular sequence.
    # Passing the seqdicts will allow tbx to print further info about the entries compared.
    tbx.printSetDiffWithStringCompare(designs[0].oligoset, designs[1].oligoset, designs[0].seqdict, designs[1].seqdict)
    #tbx.printSetDiff(designs[0].oligoset, designs[1].oligoset)
    #tbx.printSetDiffWithStringCompare(designs[0].oligoset, designs[1].oligoset)

    #tbx.PrintOrderListFromCadnanoSet('example_files/Box.Closed.jan09_c208_syncing.set')

    print "done"

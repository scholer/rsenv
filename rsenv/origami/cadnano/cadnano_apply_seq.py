#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

# pylintxx: disable-msg=C0103,C0301,C0302,R0201,R0902,R0904,R0913,W0142,W0201,W0221,W0402
# pylint: disable=C0103,C0111,R0913

"""

Apply one or more sequences to a cadnano design and export the staples (or miniscafs) produced.


Example usage:
    $> cadnano_apply_seq scafs.yaml CircFoldback_07-braced.json
    $> cadnano_apply_seq -y --export stap --export scaf scafs.yaml CircFoldback_07-braced.json
    $> cadnano_apply_seq -y --export export_oligos.yaml scafs.yaml CircFoldback_07-braced.json
    # Export oligos specified by export_oligos.yaml, applying sequences from scafs.yaml, to all
    # cadnano files matching the glob pattern *.json (verbose=1, overwriting existing files if needed):
    $> cadnano_apply_seq --export export_oligos.yaml -y -v scafs.yaml *.json

"""


import os
import sys
import glob
import argparse
import json
import yaml

# from importlib import reload
# import matplotlib
# #matplotlib.use("Qt5Agg")
# from matplotlib import pyplot, gridspec

# pylint: disable=C0103


# If you don't already have cadnano on your python path:
# Note: You can always install cadnano into your python environment using "pip install -e ."
try:
    import cadnano
except ImportError:
    CADNANO_PATH = os.environ.get("CADNANO_PATH")
    if CADNANO_PATH:
        sys.path.insert(0, os.path.normpath(CADNANO_PATH))

# Cadnano library imports
from cadnano.document import Document
from cadnano.fileio.nnodecode import decode #, decodeFile
from cadnano.part.part import Part


global VERBOSE
VERBOSE = 0


def parse_args(argv=None):
    """
    # grep implements
    #-E, --extended-regexp     PATTERN is an extended regular expression
    #-F, --fixed-strings       PATTERN is a set of newline-separated strings
    #-G, --basic-regexp        PATTERN is a basic regular expression
    #-e, --regexp=PATTERN      use PATTERN as a regular expression

    """

    parser = argparse.ArgumentParser(description="Cadnano apply sequence script.")
    parser.add_argument("--verbose", "-v", action="count", help="Increase verbosity.")
    # NOTE: Windows does not support wildcard expansion in the default command line prompt!

    #parser.add_argument("--seqfile", "-s", nargs=1, required=True, help="File containing the sequences")
    parser.add_argument("seqfile", help="File containing the sequences")

    parser.add_argument("--seqfileformat", help="File format for the sequence file.")

    parser.add_argument("--offset",
                        help="Offset the sequence by this number of bases (positive or negative). "\
                        "An offset can be sensible if the scaffold is circular, "\
                        "or you have extra scaffold at the ends and you want to optimize where to start. "
                        "Note: The offset is applied to ALL sequences, unless an individual seq_spec "
                        "specifies an offset.")

    parser.add_argument("--overwrite", "-y", action="store_true",
                        help="Overwrite existing staple files if they already exists. "
                        "(Default: Ask before overwriting)")

    parser.add_argument("--config", "-c", help="Load config from this file (yaml format). "
                        "Nice if you dont want to provide all config parameters via the command line.")

    parser.add_argument("--export", action="append", help="Which oligos to export sequence for."
                        "The default is to export staple strands. However, this script can also export e.g. "
                        "all scaffold oligos or oligos matching a given set of criteria. "
                        "Recognized values are: 'stap', 'scaf', or a filename."
                        "If a file is given, it should contain a list of criteria provided in the same way "
                        "as the criteria in a sequence file (if yaml format).")

    parser.add_argument("cadnano_files", nargs="+", metavar="cadnano_file",
                        help="One or more cadnano design files (.json) to apply sequence(s) to.")

    parser.add_argument("--output", default="{design}.staples.csv",
                        help="The filename to output the staple/scaffold sequences to. "
                        "The output filename can include python format specifies, "
                        "e.g. {design}, {cadnano_fname} and {seqfile}. "
                        "Default is {design}.staples.csv")

    return parser, parser.parse_args(argv)


def process_args(argns=None):
    """ Process command line args. """
    if argns is None:
        _, argns = parse_args()
    args = argns.__dict__.copy()
    if args.get("config"):
        with open(args["config"]) as fp:
            cfg = yaml.load(fp)
        args.update(cfg)
    # On windows, we have to expand *.json manually:
    args['cadnano_files'] = [fname for pattern in args['cadnano_files'] for fname in glob.glob(pattern)]
    return args

def load_criteria_list(filepath):
    """
    The criteria list specifies which oligos to export, and can be specified either as json or yaml.
    This will load data.
    """
    try:
        ext = os.path.splitext(filepath)[1]
    except IndexError:
        ext = "yaml"
    with open(filepath) as fd:
        criteria_list = json.load(fd) if "json" in ext else yaml.load(fd)
    return criteria_list


def load_seq(args):
    """
    I figure there are a couple of ways I'd want to specify the sequences, from low to high complexity:
    1) Just one fucking sequence.
    2) One sequence, but with an offset
    3) Several sequences.

    In the case of several sequences, I would need some way to determine which sequence to apply to which oligo.
    That could be any of:
    * Length
    * Scaffold or staple strand(set)
    * Start (5p) position vhelix[baseidx] --
    * End (3p) position vhelix[baseidx] --
    I don't think it would be too hard to make a general filtering function that could take any or all
    of these discriminators into consideration.

    This will always return a list of dicts: (The only guaranteed key is 'seq').
        [{
            seq: <sequence>,
            name: <descriptive name for sequence, mostly for the user.>
            bp: <expected length of the sequence (again, mostly for the user)>
            criteria: {
                st_type: <"scaf" or "stap">,
                length: <length>,
                vhnumber: <vhelix number>,   # or "5pvhnumber" - was previously "5pvhnum"
                5pvhcoord: (vhcoord tuple),
                idx5Prime: <base index>,    # previously "5pbaseidx"
                (same for 3p),
                }
            offset: <integer, positive or negative>,
         }, (...) ]
    """
    seqfile = args["seqfile"]
    try:
        ext = os.path.splitext(seqfile)[1]
    except IndexError:
        ext = "txt"
    if VERBOSE > 1:
        print("seqfile:", seqfile, "- ext:", ext)
    with open(seqfile) as fd:
        if "txt" in ext:
            # Treat the file as a simple txt file
            seq = next(line for line in (l.strip() for l in fd) if line and line[0] != "#")
            seq = "".join(b for b in seq.upper() if b in "ATGCU")
            seqs = [{"seq": seq,
                     "criteria": {"st_type": "scaf"}
                    }]
        elif "fasta" in ext:
            # File is fasta format
            raise NotImplementedError("Fasta files are not yet implemented. (But that is easy to do when needed.)")
        elif "yaml" in ext:
            seqs = yaml.load(fd)
        elif "json" in ext:
            seqs = json.load(fd)
        else:
            raise ValueError("seqfile extension %s not recognized format." % ext)
    return seqs


def get_part(doc):
    """ Cadnano is currently a little flaky regarding how to get the part. This tries to mitigate that. """
    try:
        # New-style cadnano:
        part = doc.selectedInstance()
    except AttributeError:
        # Old-style:
        part = doc.selectedPart()
    if VERBOSE > 1:
        print("Part:", part)
    if not isinstance(part, Part):
        if hasattr(part, "parent"):
            # part is actually just a cadnano.objectinstance.ObjectInstance
            # we need the cadnano.part.squarepart.SquarePart which is ObjectInstance.parent
            try:
                part = part.parent()
            except TypeError:
                # There are also some issues with parent being a getter or not...
                part = part.parent
        else:
            # Try something else
            part = doc.children()[0]
    return part


def crit_match(oligo, key, value):
    """ Match an oligo against a single criteria (key, value) """
    org_key = key
    if key == "st_type":
        # logical XOR: equivalent to
        # (oligo.isStaple() and value == "stap") or (not oligo.isStaple() and value == "scaf")
        return oligo.isStaple() == (value == "stap")
    # This seems efficient. Do try it for all keys:
    if key in ("length", "color", "idx5Prime", "vhnumber") or True:
        if key in ("idx5Prime", ):
            crit_obj = oligo.strand5p()
        elif key in ("vhnumber", ):
            crit_obj = oligo.strand5p().virtualHelix()
            key = key[2:]
        else:
            crit_obj = oligo
            # Allow flexible specification:
            # Specify as "5pidx5Prime" or "5pvhnumber" or "5pvhcoord"
            if key[:2] == "5p":
                crit_obj = crit_obj.strand5p()
                key = key[2:]
            if key[:2] == "vh":
                crit_obj = crit_obj.virtualHelix()
                key = key[2:]
        try:
            oval = getattr(crit_obj, key)()
        except AttributeError as e:
            print("\nERROR:", e)
        else:
            # What if length is a tuple specifying a range, e.g. (100, 150) to apply to all oligos within a certain range?
            if isinstance(value, (list, tuple)):
                if len(value) == 2:
                    return value[0] <= oval <= value[1]
                # We have a set of acceptable values:
                return oval in value
            return oval == value
    # Future criterium: sequence, ...?
    #st = oligo.strand5p()
    #if key.lower() == "5pbaseidx":
    #    return st.idx5Prime() == value
    #vh = st.virtualHelix()
    #if key.lower() == "5pvhnum":
    #    return vh.number() == value
    #if key.lower() == "5pvhcoord":
    #    # value can be either (5, 2) or it can be (5, None).
    #    # If a coordinate is None, it should match all, i.e. we are doing row/col matching only.
    #    # So e.g. we'd zip value = (5, None) with vh.coord() = (5, 2) to produce [(5, 5), (None, 2)]
    #    # and compare the equality of these or if v is None:
    #    return all(v == a or v is None for v, a in zip(value, vh.coord()))
    raise KeyError('Criteria key "%s" not recognized.' % org_key)


def match_oligo(oligo, criteria):
    """
    Returns True if oligo matches all criterium in the given set of criteria.

    See if oligo matches the given criteria.
    Criteria is a dict with any of these keys: (case insensitive)
        st_type: <"scaf" or "stap">,
        length: <length>,
        color: <hex color code>
        5pvhnum: <vhelix number>,
        5pvhcoord: (vhcoord tuple),
        5pbaseidx: <base index>,
        (same for 3p),

    Key methods for Oligo:
        applyColor(), color(), setColor()
        applySequence()
        isStaple()
        length(), setLength()
        locString()
        sequence(), sequenceExport()
        strand5p()
    Key methods for Strand:
        highIdx(), lowIdx(), idx3Prime(), idx5Prime(), idxs(),
        connection3p(), connection5p(), connectionHigh(), connectionLow(),
        generator3p(), generator5p(),
        getComplementStrands(),
        sequence(), getSequenceList(),
        strandType(), isScaffold(), isStaple,
        length(), totalLength(),
        strandSet(), oligo(), virtualHelix(), part()
        plus: insertion methods, and a lot of setters.
    """
    return all(crit_match(oligo, key, value) for key, value in criteria.items())


def get_matching_oligos(part, criteria):
    """
    Get all oligos on part matching the given set of criteria.
    Criteria is usually a set of criteria (a dict, actually) of
        criterium-key: criterium-value(s) or range, e.g.
        length: 128
    In this case, return a list of all oligos matching all criteria in the dict.
    However, criteria can also be a list of criteria dicts,
    in which case return the union (set) of all oligos fully matching
    any of the criterium dicts in the list.
    """
    # We'd usually expect only one oligo to match the set of criteria,
    # and we'd probably want to verify that exactly one oligo is matching,
    # so generate a list, not a generator.
    if isinstance(criteria, list):
        # if we have a criteria_list, return the union of oligos matching any criteria (dict) in the list:
        return {oligo for crit_dict in criteria for oligo in get_matching_oligos(part, crit_dict)}
    return [oligo for oligo in part.oligos() if match_oligo(oligo, criteria)]


def print_oligo_criteria_match_report(oligos, criteria, desc=None):
    """ Print standard criteria match report. """
    print("\n{} oligos matching criteria set {}:".format(len(oligos), desc))
    #print("Oligos matching criteria set:", desc)
    if VERBOSE > 1 or not oligos:
        print(yaml.dump({"criteria": [criteria]}, default_flow_style=False).strip("\n"))
        print("The matching oligos are:")
        print("\n".join(" - {}".format(oligo) for oligo in oligos))


def apply_sequences(part, seqs, offset=None):
    """ Apply sequences in seqs to oligos in part. """
    # Apply sequence:
    #with open(os.path.join(folder, sequence_file)) as fd:
    #    scaf_sequence = fd.read()
    #scaf_oligo = next(oligo for oligo in part.oligos() if not oligo.isStaple())
    for seq_i, seq_spec in enumerate(seqs):
        # seq_spec has key "seq" and optional keys "criteria", and "offset".
        seq = seq_spec["seq"]
        L = len(seq)
        seq_offset = seq_spec.get("offset", offset)
        if seq_offset:
            seq = (seq*3)[L+seq_offset:L*2+seq_offset]
        oligos = get_matching_oligos(part, seq_spec["criteria"])
        if VERBOSE > 1 or not oligos:
            if not oligos:
                print("\n\nNOTICE! The following oligo criteria (selection for apply) did not match any oligos:")
            print_oligo_criteria_match_report(oligos, seq_spec["criteria"],
                                              desc="for application of sequence #{}".format(seq_i))
        for oligo in oligos:
            oligo.applySequence(seq, use_undostack=False)


def ok_to_write_to_file(staples_outputfn, args):
    """ Assert whether it is OK to write to staples_outputfn """
    if args["overwrite"] or not os.path.exists(staples_outputfn):
        return True
    # os.path.exists(staples_outputfn) is True
    overwrite = input(staples_outputfn + " already exists. Overwrite? [Y/n]")
    if overwrite and overwrite.lower()[0] == "n":
        return False
    return True


def get_export_criteria_list(args):
    """
    Returns a list of criteria sets. Each criteria set can match one or more oligos.
    The criteria_list is usually used to generate a list/set of oligos matching
    any of the criteria (set) in the list, but matching all criterium in that criteria set,
    basically:
        include_oligo = any(all(match_crit(oligo, criterium) for criterium in criteria)
                            for criteria in criteria_list)
    """
    if args['export'] is None:
        return None
    # Alternative generation with list comprehension:
    criteria_list = [criteria for export in args['export'] for criteria in
                     ([{"st_type": export}] if export in ("scaf", "stap") else load_criteria_list(export))]
    ## Original:
    #criteria_lst2 = []
    #for export in args['export']:
    #    if export in ("scaf", "stap"):
    #        criteria_lst2.append({"st_type": export})
    #    else:
    #        criteria_lst2 += load_criteria_list(export)
    #if not criteria_list == criteria_lst2:
    #    print("criteria_list != criteria_lst2  !!")
    return criteria_list


def export_oligo_seqs(part, csvfilepath=None, criteria_list=None):
    """
    Export all oligos from part, matching the any of the set of criteria in criteria_list.
    criteria_list enables you to have a list of criteria-set, so that you can export both:
            all staples,
        and some scaffolds that are read,
        and scaffold oligos on vhelix 2

    Criteria takes the same format as for applying sequence,
    see match_oligo()
    If criteria is None, then all sequences for all staples will be exported.
    """
    # export staples:
    if criteria_list is None:
        csv_text = part.getStapleSequences()
    else:
        #oligos = {oligo for criteria in criteria_list for oligo in get_matching_oligos(part, criteria)}
        oligos = get_matching_oligos(part, criteria_list)
        if VERBOSE > 2:
            print_oligo_criteria_match_report(oligos, criteria_list, desc="for export")
        header = "Start,End,Sequence,Length,Color,5pMod,3pMod\n"
        csv_text = header + "".join(oligo.sequenceExport() for oligo in oligos)
    with open(csvfilepath, "w") as fd:
        n = fd.write(csv_text)
        if VERBOSE > 0:
            print("\n{} bytes written to file: {}\n".format(n, csvfilepath))



def main(argv=None):
    global VERBOSE
    args = process_args(argv)
    VERBOSE = args['verbose'] or 0

    # Get sequence(s):
    seqs = load_seq(args)
    # What to export:
    export_criteria_list = get_export_criteria_list(args)
    if VERBOSE > 1:
        print("export criteria list:")
        print(yaml.dump(export_criteria_list))

    for cadnano_file in args["cadnano_files"]:
        # folder = os.path.realpath(os.path.dirname(cadnano_file))
        # "141105_longer_catenane_BsoBI-frag_offset6nt.json"
        design = os.path.splitext(os.path.basename(cadnano_file))[0]
        staples_outputfn = args["output"].format(design=design, cadnano_file=cadnano_file, seqfile=args["seqfile"])
        if not ok_to_write_to_file(staples_outputfn, args):
            print("Aborting staple file write for file", cadnano_file)
            continue
        print("\nLoading design:", design)
        doc = Document()
        with open(cadnano_file) as fp:
            nno_dict = json.load(fp)
        decode(doc, nno_dict)
        print(cadnano_file, "loaded!")
        part = get_part(doc)
        apply_sequences(part, seqs, offset=args.get("offset")) # global offset
        export_oligo_seqs(part, csvfilepath=staples_outputfn, criteria_list=export_criteria_list)




if __name__ == '__main__':
    main()

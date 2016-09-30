"""

Annoyingly, IDT's CoA especs have a tri-nucleotide spaced sequence values, i.e. "TGC TGC AGG TCG TTC GTT CA".

This makes it hard to grep for sequences.
This script will take a csv file, look for the sequence field, remove spaces in the sequence, and save the file.

"""


import os
import sys
import argparse


def reformat_coa_csv(inputfn, outputfn, seqfield='"Sequence"', sep_in=None, sep_out=None, sep_default="\t",
                     seq_formatter=lambda seq: seq.replace(" ", "")):
    """Reformat input csv file, printing to outputfn."""

    nlines = 0
    with (open(inputfn) if inputfn is not None else sys.stdin) as fin:
        with (open(outputfn, 'w') if outputfn is not None else sys.stdout) as fout:
            headerline = next(fin)
            if sep_in is None:
                sep_in = next((mark for mark in ("\t", ",", ";") if mark in headerline), sep_default)
            if sep_out is None:
                sep_out = sep_in
            headers = [header.strip() for header in headerline.split(sep_in)]  # Remember to strip to remove '\n'
            seq_idx = headers.index(seqfield)
            fout.write(sep_out.join(headers) + "\n")
            for line in fin:
                row = [field.strip() for field in line.split(sep_in)]
                row[seq_idx] = seq_formatter(row[seq_idx])
                fout.write(sep_out.join(row) + "\n")
                nlines += 1
    return nlines


def reformat_bulk(inputfiles, outputdir=None, fnfmt="{fnroot}_stripped{ext}", read_stdin=False, write_stdout=False):
    """Bulk reformatting of multiple input files."""

    if outputdir:
        outputdir = os.path.expanduser(outputdir)
        if not os.path.exists(outputdir):
            print("%s does not exists - trying to create..." % (outputdir, ))
            os.mkdir(outputdir)
    elif outputdir is None:
        outputdir = "."

    n_processed = 0
    for inputfn in inputfiles:
        if outputdir is None:
            fnroot, fnext = os.path.splitext(inputfn)
        else:
            fnroot, fnext = os.path.splitext(os.path.basename(inputfn))  # basename = "filename without directory"
        outputfn = fnfmt.format(fn=inputfn, fnroot=fnroot, ext=fnext)
        if outputdir:
            outputfn = os.path.join(outputdir, outputfn)

        print("Reformatting CoA file:", inputfn)
        nlines = reformat_coa_csv(inputfn, outputfn)
        print(" - %04s lines written: %s" % (nlines, outputfn))
        n_processed += 1
    return n_processed


def make_parser(args):
    ap = argparse.ArgumentParser(prog="Reformat CSV")
    ap.add_argument("inputfiles", nargs="*")
    ap.add_argument("--outputdir")
    ap.add_argument("--fnfmt", default="{fnroot}_stripped{ext}")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    return ap


def main(args=None):

    # Parse command line arguments:
    ap = make_parser(args)
    argns = ap.parse_args(args)

    # Perform data reformatting:
    n_processed = reformat_bulk(argns.inputfiles, argns.outputdir, argns.fnfmt)
    print("\n\nDone! %s files was processed.\n" % (n_processed,))


# run-alone entry point:
if __name__ == '__main__':
    main()

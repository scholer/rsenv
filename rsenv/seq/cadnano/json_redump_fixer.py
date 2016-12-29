#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
#


import os
import json
import argparse


def json_fix_eval_redump(fn, outfmt="{0}_redump{1}"):
    """Fix faulty

    :param fn:
    :return:
    """
    outfn = outfmt.format(*os.path.splitext(fn))
    with open(fn) as fdin:
        doc = fdin.read()
    doc = eval(doc)
    print(" - %s loaded..." % fn)
    with open(outfn, 'w') as fdout:
        json.dump(doc, fdout)
    print(" - json re-dumped to file %s." % (outfn,))


def make_parser(defaults=None):
    if defaults is None:
        defaults = {}
    parser = argparse.ArgumentParser(
        prog="json_redump_fixer")
    parser.add_argument('files', nargs="+")
    parser.add_argument('--outfmt', default="{0}_redump{1}")
    return parser


def parse_args(argv=None):
    parser = make_parser()
    argns = parser.parse_args(argv)
    return argns


def main(args=None, argv=None):

    if args is None:
        args = vars(parse_args(argv))

    for fn in args['files']:
        print("Fixing %s ..." % (fn,))
        json_fix_eval_redump(fn, args['outfmt'])
        print(" - done!\n")


if __name__ == '__main__':
    main()

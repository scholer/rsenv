#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

# pylintxx: disable-msg=C0103,C0301,C0302,R0201,R0902,R0904,R0913,W0142,W0201,W0221,W0402
# pylint: disable=C0103,C0111,R0913

"""

Grep IDT espec csv files for sequence.

Example usage:

    # Print oligos with 5' modification (/5Phos/):
    $> espec_grep -c seq_with_mods 5Pho *.csv --printfmt "{row[Sales Order]}
        {row[Sequence Name]} ({row[Bases]}) {row[seq_with_mods]}"

    # Find oligos with "5Phos" mod and "rss" in sequence name, printing all matching oligos as
    #   <sales order> <Sequence Name> <Bases> <Sequence with mods> <Mods and services>
    # searching all *.csv files and using the csv module to parse the csv files:
    # (using the csv module is not compatible with the simple line-based --regex option,
    # but it is currently needed for proper, quoted, parsing if any fields contain a comma)
    $> espec_grep -c seq_with_mods 5Phos --csv --criteria "Sequence Name" rss
        --printfmt "{row[Sales Order]} {row[Sequence Name]} ({row[Bases]}) {row[seq_with_mods]}
        {row[Modifications and Services]}" *.csv

"""


#import os
import sys
import argparse
import glob
import string
import csv


# Module-level constants:
seq_mods_chars = string.digits+string.ascii_letters+string.punctuation


def parse_args(argv):
    """
    # grep implements
    #-E, --extended-regexp     PATTERN is an extended regular expression
    #-F, --fixed-strings       PATTERN is a set of newline-separated strings
    #-G, --basic-regexp        PATTERN is a basic regular expression
    #-e, --regexp=PATTERN      use PATTERN as a regular expression

    """

    parser = argparse.ArgumentParser()

    #"{}:{} {}"
    parser.add_argument('--printfmt', default="{filepath}:{lineno} {line}",
                        help="Default format string for printing matches. "\
                             "Valid fields are filepath, lineno, line, and row. "\
                             "Default is {filepath}:{lineno} {line}. "
                             "Inspiration: {filepath: <40}: {row[Sequence Name]: >20} {row[seq]}")

    parser.add_argument('--verbose', '-v', action="count", help="Increase verbosity.")


    # Flags for how to match the regexp pattern
    parser.add_argument('--extended-regexp', '-E', action='store_true',
                        help="Matching style is: PATTERN is an extended regular expression")
    parser.add_argument('--fixed-strings', '-F', action='store_true',
                        help="PATTERN is a set of newline-separated strings")
    parser.add_argument('--basic-regexp', '-G', action='store_true', help="PATTERN is a basic regular expression")

    # The regex pattern
    parser.add_argument('--regexp', '-e', metavar="PATTERN",
                        help="PATTERN is the string/regular expression used to match.")

    # Actually, this seems familiar. I think I made a grep script once which used --criteria <field> <operator> <value>
    # e.g. --criteria conc lt 100  # where lt is "less than".
    parser.add_argument('--sep', default=",", help="Field separator.")
    parser.add_argument('--csv', action='store_true', help="Use csv module to parse csv files. "\
                        "This enables features such as quote and comma/separator inside fields. "\
                        "Unfortunately, the (line-based) --regexp argument cannot be used together with --csv.")
    parser.add_argument('--dialect', help="The csv dialect to use, e.g. 'excel', 'excel-tab' or 'unix'")

    parser.add_argument('--criteria', '-c', nargs=2, action='append', metavar=("FIELD", "PATTERN"), help="")
    parser.add_argument('--seq', help="Short-hand for -c seq <SEQ>")


    # NOTE: Windows does not support wildcard expansion in the default command line prompt!
    parser.add_argument('files', nargs='*', help="")


    return parser.parse_args(argv), parser



def csv_to_dictlist():
    pass


def adjust_seq(row):
    """ Add seq and seq_with_mods fields to row. """
    row['seq'] = ''.join(b for b in row['Sequence'].upper() if b in 'ATGC')
    row['seq_with_mods'] = ''.join(b for b in row['Sequence'] if b in seq_mods_chars)



def files_match_gen(files, line_regexp, criteria, match_style="fixed-strings", sep=",", use_csv=None, dialect=None):
    """
    Args:
        files   : files to search
        line_regexp: basic (fast) matching of line.
        Criteria: list of dicts with <field>: regexp pattern for field.

    Returns a generator of tuples with entries:
        file    : The file that was matched
        lineno  : The line number that produced the match.
        line    : The line that produced the match.
        fields  : (conditional) dict with the fields. Only if criteria was used.
    """
    # Make matcher depending on the match_style

    # Make line_matcher:
    def line_matcher(line):
        """ Closure. """
        return line_regexp in line
    # Make criteria_matcher and match function:
    if criteria:
        if isinstance(criteria, dict):
            def criteria_matcher(row):
                """ Row is the csv-parsed line as a dict. criteria is a dict. """
                return all(value in row[key] for key, value in criteria.items())
        else:
            def criteria_matcher(row):
                """ Row is the csv-parsed line as a dict. criteria is a list of (key, value) tuples. """
                return all(value in row[key] for key, value in criteria)
        if line_regexp:
            def match(line, row):
                return line_matcher(line) and criteria_matcher(row)
        else:
            def match(line, row):
                return criteria_matcher(row)
    else:
        if not line_regexp:
            raise ValueError("You must provide either a line regexp (--regexp) or one or more criteria.")
        def match(line, row=None):
            return line_matcher(line)
    for filepath in files:
        headers = None
        header_warning = None
        with open(filepath) as fd:
            #lines = (line for line in fd)
            if use_csv:
                # Use csv. line regex will not be available.
                if line_regexp:
                    raise ValueError("line_regexp cannot be used in conjunction with --csv switch.")
                if not dialect:
                    dialect = csv.Sniffer().sniff(fd.read(4*1024))
                    fd.seek(0)
                reader = csv.DictReader(fd, dialect=dialect)
                for lineno, row in enumerate(reader, 1):
                    try:
                        adjust_seq(row)
                    except KeyError:
                        if not header_warning:
                            print("Sequence header not found in file", filepath, "\n - header is:", headers)
                            header_warning = True
                    if criteria_matcher(row):
                        yield (filepath, lineno, "<Line not available with --csv switch>", row)
            else:
                # Simple csv parsing; do not use csv module.
                for lineno, line in enumerate(fd, 1):
                    if not line.strip():
                        continue    # Don't try to match empty lines...
                    if criteria:
                        # Only parse line as comma-separated-values if neeeded...
                        if headers is None:
                            ## simply doing line.split(sep) causes issues if e.g. Sequence Name includes the sep.
                            ## Using the csv module is currently required to handle these special cases...
                            headers = [header.strip('\t "') for header in line.split(sep)]
                            continue    # We are not matching header lines
                        row = {header: cell.strip('\t "') for header, cell in zip(headers, line.split(sep))}
                        # Probably also want to do some extra stuff, e.g. make stripped sequence field:
                        try:
                            adjust_seq(row)
                        except KeyError:
                            if not header_warning:
                                print("Sequence header not found in file", filepath, "\n - header is:", headers)
                                header_warning = True
                    else:
                        row = {}
                    if match(line, row):
                        yield (filepath, lineno, line.strip('\n'), row)



#def line_match_printer(match_tuple):
#    #print("{}:{} {}".format(filepath, lineno, line))
#    print("{}:{} {}".format(*match_tuple))


def expand_files(files):
    """
    Windows does not allow wildcard expansion at the prompt. Do this.
    """
    expanded = [fname for pattern in files for fname in glob.glob(pattern)]
    return expanded


def ascii_filter(*args):
    return ("".join(c for c in arg if c in string.printable) if isinstance(arg, str) else arg
            for arg in args)



def main(argv=None):
    """
    #-E, --extended-regexp     PATTERN is an extended regular expression
    #-F, --fixed-strings       PATTERN is a set of newline-separated strings
    #-G, --basic-regexp        PATTERN is a basic regular expression

    #-e, --regexp=PATTERN      use PATTERN as a regular expression


    Standard IDT especs header is:
    "Sales Order","Reference","Manufacturing ID","Product","Purification","Sequence Name","Sequence Notes","Unit Size",
    "Bases","Sequence","Anhydrous Molecular Weight","nmoles/OD","ug/OD","Extinction Coefficient","GC Content",
    "Tm (50mM NaCl) C","Modifications and Services","Final OD","nmoles","Print Date","Well Position"

    """
    argsns, parser = parse_args(argv)
    if argsns.verbose and argsns.verbose > 2:
        print("sys.argv:", sys.argv)
        print("argsns:", argsns)

    # , criteria, match_method="fixed-strings", sep=","
    match_style = next((att for att in ('extended_regexp', 'fixed_strings', 'basic_regexp')
                        if getattr(argsns, att)), 'fixed_strings')
    files = expand_files(argsns.files)
    if not files:
        print("No files specified! -", files)
        sys.exit(1)
    if argsns.seq:
        argsns.criteria = (argsns.criteria or []) + [("seq", argsns.seq)]
    print("Criteria:", argsns.criteria)
    line_matches = files_match_gen(files=files,
                                   line_regexp=argsns.regexp,
                                   criteria=argsns.criteria,
                                   match_style=match_style,
                                   sep=argsns.sep,
                                   use_csv=argsns.csv,
                                   dialect=argsns.dialect,
                                  )
    try:
        for filepath, lineno, line, row in line_matches:
            # print(", ".join("{0}={0}".format(val) for val in "filepath, lineno, line, row".split(", ")))
            try:
                print(argsns.printfmt.format(filepath=filepath, lineno=lineno, line=line, row=row))
            except UnicodeEncodeError:
                filepath, lineno, line, row = ascii_filter(filepath, lineno, line, row)
                print(argsns.printfmt.format(filepath=filepath, lineno=lineno, line=line, row=row))
                print("## Not all values could be properly printed in the above line ##")
    except ValueError as e:
        print(e)
        parser.print_help()

if __name__ == '__main__':
    main()

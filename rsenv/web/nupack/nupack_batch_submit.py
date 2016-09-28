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

Submit sequences for nupack analysis to Nupack.org

Example usage:
    # Load general/common parameters from general_config.yaml, then for each entry
    # in sequences.csv submit a nupack partition analysis request:
    $> python nupack_batch_submit.py -c general_config.yaml --batch seqeuences.csv



"""


#import os
#import sys
import argparse
import glob
import string
#import csv
import yaml
import requests
import webbrowser
import re
import time
from datetime import datetime


# Module-level constants:
seq_mods_chars = string.digits+string.ascii_letters+string.punctuation
verbose = 0

def parse_args(argv):
    """
    Parse command line arguments.
    """

    parser = argparse.ArgumentParser()

    #"{}:{} {}"
    #parser.add_argument('--printfmt', default="{filepath}:{lineno} {line}",
    #                    help="Default format string for printing matches. "\
    #                         "Valid fields are filepath, lineno, line, and row. "\
    #                         "Default is {filepath}:{lineno} {line}. "
    #                         "Inspiration: {filepath: <40}: {row[Sequence Name]: >20} {row[seq]}")

    parser.add_argument('--verbose', '-v', action="count", help="Increase verbosity.")


    # Actually, this seems familiar. I think I made a grep script once which used --criteria <field> <operator> <value>
    # e.g. --criteria conc lt 100  # where lt is "less than".
    parser.add_argument('--sep', help="Field separator.")
    parser.add_argument('--sleep', type=int, default=2, help="Wait this number of seconds between each request.")
    parser.add_argument('--browser', action="store_true", help="Open nupack page in browser for every batch request.")
    parser.add_argument('--print_jobparams', action="store_true",
                        help="Print all job parameters (both general and for each sequence batch).")

    parser.add_argument('--savetofile', help="Save tokens and urls to this file (using outputfmt). "
                        "Various format specifiers are available, e.g. {date:yyyy-mm-dd HH:MM} and {batch}")
    parser.add_argument('--outputfmt', default="{token}, {r.url}",
                        help="Save token and url for every batch job using this format. "
                        "{r} is response and {token} is token.")
    parser.add_argument('config', help="File with common job parameters.")
    parser.add_argument('batch', help="Load sequence batches from this file, "
                        "and submit each one for nupack.org partition analysis. "
                        "The batches are separated by an empty line (\\n\\n). "
                        "Each batch consists of one or more lines, one line per sequence/specie. "
                        "The parameter on the sequence line is separated by a whitespace (can be changed with --sep), "
                        "in the order: Name, Sequence, Concentration, Scale "
                        "Where Name is name of the specie, Sequence is the sequence/content, "
                        "Concentration is a numeric value, and scale is the molar magnitude, "
                        "e.g. -6 for uM, -9 for nM and so forth.")
    # NOTE: Windows does not support wildcard expansion in the default command line prompt!
    #parser.add_argument('files', nargs='*', help="")

    return parser.parse_args(argv), parser

def expand_files(files):
    """
    Windows does not allow wildcard expansion at the prompt. Do this.
    """
    expanded = [fname for pattern in files for fname in glob.glob(pattern)]
    return expanded


def read_seqs(file):
    """
    name: 'strand1'
contents: ''
concentration: '1'
scale: '-6'
    File format is:
    # name      seq/contents [concentration]    [scale]
    batch1seq1  TCAAAAGCGCTTTTGCGCTTTTGT    100  -9
    batch1seq2  ACAAAAGCGCAAAAGCGCTTTTGA

    batch2seq1 ...
    batch2seq2 ...
    """
    with open(file) as fp:
        content = fp.read()
    batches = [[dict(zip(("name", "contents", "concentration", "scale"), seq_line.split()))
                for seq_line in batch_section.split("\n") if seq_line.strip()]  # Do not include empty lines
               for batch_section in content.split("\n\n")]
    return batches

def load_yaml(filepath):
    """ Load yaml from filepath """
    with open(filepath) as fp:
        r = yaml.load(fp)
    return r


def get_defaults():
    partition_sequence = yaml.load("""
name: 'strand1'
contents: ''
concentration: '1'
scale: '-6'
""")
    partition_job = yaml.load("""
nucleic_acid_type: 'DNA'
temperature: '37.0'
is_melt: '0'
min_melt_temperature: ''
melt_temperature_increment: ''
max_melt_temperature: ''
num_sequences: '1'
max_complex_size: '1'
rna_parameter_file: 'rna1999'
dna_parameter_file: 'dna1998'
dangle_level: '1'    # 0, 1, 2 for None, Some, All
pseudoknots: '0'    # Currently disabled.
na_salt: '1.0'
mg_salt: '0.0'
dotplot_target: '1'
predefined_complexes: '' # Text area input
filter_min_fraction_of_max: ''
filter_max_number: ''
email_address: ''
""")
    return partition_job, partition_sequence


def gen_data(job_param, sequences_params):
    """
    job_params is a dict with partition_job parameters
    sequences_params is a list of sequence parameters.

    See notes/nupack.org_form_parsing.py for notes on the form inputs
    """
    data = {}
    job_fmt = "partition_job[{}]"
    seq_fmt = "partition_sequence[{}][{}]"
    for key, value in job_param.items():
        data[job_fmt.format(key)] = value
    for i, seq_param in enumerate(sequences_params):
        for key, value in seq_param.items():
            data[seq_fmt.format(i, key)] = value
    return data


def dispatch(job_param, sequences_params, session=None):
    """
    Dispatch request using parameters form job_param and sequences_params
    Arguments:
        job_params is a dict with partition_job parameters
        sequences_params is a list of sequence parameters.
    Returns the request object.
    Usage example:
        >>> dispatch({...}, [{...}, ...])
    Note: You might get a "ConnectionError" if using requests version < 2.7.
    If you do, just upgrade your version of requests.
    """
    url = "http://nupack.org/partition/new"     # no https...
    if isinstance(sequences_params, dict):
        sequences_params = [sequences_params]
    if int(job_param["max_complex_size"]) > 1:
        if any("concentration" not in seq_param for seq_param in sequences_params):
            print("Sequence batch contains one or more sequence lines with no concentration. "
                  "Concentraion is required for max_complex_size > 1.")
            raise KeyError("Missing concentration for sequence batch (max_complex_size > 1)")
    if any(not seq_param.get("contents") or not seq_param.get("name") for seq_param in sequences_params):
        print("One or more sequences with empty name or sequence-content!")
        raise ValueError("Missing name or sequence for sequence batch")
    for seq_param in sequences_params:
        if "scale" not in seq_param or seq_param["scale"] is None:
            if verbose > 0:
                print("Adjusting seq_param[scale] to -6 (uM)")
            seq_param["scale"] = "-6"
    data = gen_data(job_param, sequences_params)
    if session is None:
        session = requests.Session()
    r = session.post(url, data)
    return r



def get_tokens(responses):
    """ Find tokens in response urls. """
    tok_regex = re.compile(r"token=(\w+)")
    tokens = [match.group(1) if match else "No token for {} (Code {})".format(r.url, r.status_code)
              for match, r in ((tok_regex.search(r.url), r) for r in responses)]
    return tokens


def save_tokens(responses, outputfn, outputfmt="{token}"):
    """ Save tokens to file. """
    tokens = get_tokens(responses)
    with open(outputfn, 'w') as fp:
        fp.write("\n".join(outputfmt.format(token=token, r=response)
                           for token, response in zip(tokens, responses)))


def main(argv=None):
    """
    Submit
    """
    argns, _ = parse_args(argv)
    seq_batches = read_seqs(argns.batch)
    global verbose
    verbose = argns.verbose or 0

    job_param, def_seq_param = get_defaults()
    if argns.config:
        job_param.update(load_yaml(argns.config))
    s = requests.Session()
    N_jobs = len(seq_batches)
    responses = []

    if argns.print_jobparams:
        print("General job parameters for all batches:")
        print(yaml.dump(job_param, default_flow_style=False))

    for i, seq_batch in enumerate(seq_batches, 1):
        print("\n\nProccessing sequence batch {} of {}".format(i, N_jobs))
        if argns.print_jobparams:
            print("Sequence batch parameters:")
            print(yaml.dump(seq_batch, default_flow_style=False))
        if not len(seq_batch) == int(job_param["num_sequences"]):
            print("Adjusting num_sequences to:", len(seq_batch))
            job_param["num_sequences"] = str(len(seq_batch))
        print("Dispatching batch {} of {}...".format(i, N_jobs))
        r = dispatch(job_param, seq_batch, session=s)
        time.sleep(argns.sleep)
        print("Got response: {} - URL: {}".format(r, r.url))
        responses.append(r)
        if argns.browser:
            webbrowser.open(r.url)

    if argns.savetofile:
        outputfn = argns.savetofile.format(date=datetime.now(), batch=argns.batch)
        save_tokens(responses, outputfn, argns.outputfmt)
        print("\nTokens saved to file:", outputfn)

    print("\nDONE!")





if __name__ == '__main__':
    main()

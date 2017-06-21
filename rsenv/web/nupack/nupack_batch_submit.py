#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    Copyright 2015-2017 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
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

Submit sequences for nupack analysis to Nupack.org

Command line usage:
--------------------

    To get help:
        $ python nupack_batch_submit.py --help

    Or, if rsenv is installed in current python environment:
        $ python -m rsenv.web.nupack.nupack_batch_submit --help



Typical command line usage:

    $ python nupack_batch_submit.py --jobparams general_config.yaml seqeuences.csv

Detailed usage description:

    First define which sequences to analyze:
        1. Create a new text file, `sequences.csv`.
        2. Add one sequence per line, as follows: (default is whitespace-delimited values)

            # name      seq/contents             [conc]    [conc_scale]
            batch1seq1  TCAAAAGCGCTTTTGCGCTTTTGT    100    -9
            batch1seq2  ACAAAAGCGCAAAAGCGCTTTTGA      1    -6

            batch2seq1  TCAAAAGCGCTTTTGCGCTTTTGT     10    -6
            batch2seq2  GGGAAAGCGCAAAAGCGCTTTTGA      1    -6

    Second, place computational parameters in a yaml-formatted file, e.g. `general_config.yaml`,
    c.f. the NuPack job parameters list below.

    Then run the script:

        $ python nupack_batch_submit.py --jobparams general_config.yaml seqeuences.csv

    The script will (1) Load general/common parameters from general_config.yaml,
    and (2) then for each batch in sequences.csv submit a nupack partition analysis request:


OBS: After the job completes, you can use the `nupack_download_job` module to download and extract all job files:

    $ python -m rsenv.web.nupack.nupack_download_job jobtokenslist.yaml --unzip



Python/library usage:
---------------------

Example, using this module/functions from Python:

    >>> from rsenv.web.nupack.nupack_batch_submit import parse_sequence_batch_file, dispatch
    >>> batches = parse_sequence_batch_file('sequences.csv')
    >>> job_param = dict(nucleic_acid_type='DNA', temperature='37.0')  # etc
    >>> for seq_batch in batches:
    >>>     response = dispatch(job_param=job_param, sequences_params=batches)

Alternatively, using `submit_batches()`:
    >>> # batches: either a file with sequence batches information (c.f. sequence batch file content example below),
    >>> # or a list of sequence batches, e.g. a single batch with a single strand "strand1" in 1 uM concentration:
    >>> batches = [[{'name': 'strand1', 'contents': 'GCTTTTCCCTTTTGGGGTTTTGG', 'concentration': '1', 'scale': '-6'}]]
    >>> responses = submit_nupack_partition_jobs(
    >>>     seq_batches=batches, job_param=job_param, savetokenstofile='tokens.txt')


Example sequence batch file content:
------------------------------------
# name      seq/contents             [conc]    [conc_scale]
batch1seq1  TCAAAAGCGCTTTTGCGCTTTTGT    100    -9
batch1seq2  ACAAAAGCGCAAAAGCGCTTTTGA      1    -6

batch2seq1  TCAAAAGCGCTTTTGCGCTTTTGT     10    -6
batch2seq2  GGGAAAGCGCAAAAGCGCTTTTGA      1    -6



NuPack partition analysis job parameters and example values:
------------------------------------------------------------

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


Tips & Tricks for investigating web interfaces:
* In Chrome's developer tools panel, select "Network", then filter by `method:POST` to see POST requests.



"""


# import os
# import sys
# import csv
# import glob
import argparse
import string
import yaml
import requests
import webbrowser
import re
import time
from datetime import datetime
from pprint import pprint  # , pformat

# Local imports:
from .nupack_job_utils import token_from_url, jobid_from_url


# Module-level constants:
seq_mods_chars = string.digits + string.ascii_letters + string.punctuation
SEQ_FILE_HEADER = ("name", "contents", "concentration", "scale")
NUPACK_PARTITION_ANALYSIS_URL = "http://nupack.org/partition/new"     # no https...
TOKEN_REGEX = re.compile(r"token=(\w+)")
# verbose = 0

default_partition_sequence_params = yaml.load("""
name: 'strand1'
contents: ''
concentration: '1'
scale: '-6'
""")

default_partition_job_params = yaml.load("""
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


def load_yaml(filepath):
    """ Load yaml from filepath (reference function). """
    with open(filepath) as fp:
        r = yaml.load(fp)
    return r


def parse_sequence_batch_file(file, sep=None):
    """Read sequence batches from file.

    Arguments:
        file: Filename for file with sequence batch(es) information.
        sep: Field separation character. Default (None) = all whitespace characters.

    Returns:
        A list of batches, each batch being a list of dicts, each dict specifying a sequence to analyze.
        (A list of lists with dicts.)

    Sequence batches file format is:

        # name      seq/contents              [conc]    [scale]
        batch1seq1  TCAAAAGCGCTTTTGCGCTTTTGT    100      -9
        batch1seq2  ACAAAAGCGCAAAAGCGCTTTTGA      1      -6

        batch2seq1 ...
        batch2seq2 ...

    The returned dicts has keys/values (example):
        {name: 'strand1', contents: '<ATGC sequence>', concentration: '1', scale: '-6'}

    """
    with open(file) as fp:
        content = fp.read()
    batches = [[dict(zip(SEQ_FILE_HEADER, seq_line.split(sep)))
                for seq_line in batch_section.split("\n")
                if seq_line.strip() and seq_line[0] != '#']  # Do not include empty lines or lines beginning with '#'
               for batch_section in content.strip().split("\n\n")]

    return batches


def seq_batch_from_design_output_file(file):
    design_output = yaml.load(open(file))
    batch = [{'name': strand['Name'], 'contents': strand['Sequence']} for strand in design_output['Strands']]
    return batch


def get_defaults():
    """Get default parameters."""
    return default_partition_job_params, default_partition_sequence_params


def gen_data(job_param, sequences_params):
    """Generate a data dictionary with valid key/value pairs that can be `post`ed by requests to the NuPack URL.

    Args:
        job_param: dict with partition_job parameters
        sequences_params: list of sequence parameters (list of dicts, one dict for each sequence)

    Returns:
        dict with NuPack web form-compatible `partition_job` and `partition_sequence` keys.

    Background:
        The NuPack web service uses the default/standard `application/x-www-form-urlencoded` format
        to encoded the web form user-input data. (See W3C docs on `x-www-form-urlencoded`.)

        However, the way the server parses the post data is a little unusual:
        Job parameters must be formatted as: `partition_job[<key>]`
        Sequence data must be formatted as: `partition_sequence[<idx>][<key>]`

        Note that this is only to get the keys correctly formatted;
        requests takes care of creating the urlencoded request body from the Python dict.

        See notes/nupack.org_form_parsing.py for notes on the form inputs.
        (Or just inspect the NuPack web form, it is pretty straight-forward.)

    """
    data = {}
    job_fmt = "partition_job[{}]"
    seq_fmt = "partition_sequence[{}][{}]"
    for key, value in job_param.items():
        data[job_fmt.format(key)] = value
    for i, seq_param in enumerate(sequences_params):
        for key, value in seq_param.items():
            data[seq_fmt.format(i, key)] = str(value)
    return data


def dispatch(job_param, sequences_params, session=None, url=NUPACK_PARTITION_ANALYSIS_URL, verbose=0):
    """Dispatch NuPack partition analysis request using parameters form `job_param` and `sequences_params`.

    Arguments:
        job_param: dict with partition_job parameters
        sequences_params: list of sequence parameters.
        session: A requests.Session to use when `POST`ing the request. If None is provided, a new Session is created.
        url: The NuPack webservice URL to post/submit the job data/parameters to.

    Returns:
        Response object.

    Usage example:

        >>> job_param = dict(nucleic_acid_type='DNA', temperature='37.0', max_complex_size='1', na_salt='1.0')  # etc.
        >>> seq_param = [
        >>>     {'name': 'strand1', 'contents': 'GCTTTTCCCTTTTGGGGTTTTGG', 'concentration': '1', 'scale': '-6'},
        >>>     # ... other strands
        >>> ]
        >>> res = dispatch(job_param, seq_param)  # response object

    Note: You might get a "ConnectionError" if using requests version < 2.7.
    If you do, just upgrade your version of requests.

    """
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
            if verbose and verbose > 0:
                print("Adjusting seq_param[scale] to -6 (uM)")
            seq_param["scale"] = "-6"
    data = gen_data(job_param, sequences_params)
    if session is None:
        session = requests.Session()
    if verbose and verbose > 1:
        print("\ndata to be POSTed:")
        pprint(data)
        print("\nSession headers, cookies:")
        print(session.headers)
        print()
        print(session.cookies)
        print()
    # raise RuntimeError("debug")
    r = session.post(url, data)
    return r


def jobinfo_from_url(url):
    return {
        'jobid': jobid_from_url(url),
        'token': token_from_url(url),
    }
    # d['token'] = token_from_url(response.url)
    # d['jobid'] = jobid_from_url(response.url)


def response_to_job_dict(response, attrs = ('url', 'status_code', 'reason'), history=True):
    d = {att: getattr(response, att) for att in attrs}
    if history:
        d['history'] = [response_to_job_dict(r) for r in response.history]
    d.update(jobinfo_from_url(response.url))
    return d


def responses_to_yaml(responses, stream=None):
    response_dicts = [response_to_job_dict(res) for res in responses]
    return yaml.dump(response_dicts)


def get_tokens(responses):
    """ Find tokens in response urls. """
    tokens = [match.group(1) if match else "No token for {} (Code {})".format(r.url, r.status_code)
              for match, r in ((TOKEN_REGEX.search(r.url), r) for r in responses)]
    return tokens


def get_jobids(responses):
    jobids = [jobid_from_url(r.url) for r in responses]
    return jobids


def extract_and_format_tokens(responses, outputfmt="{token}"):
    """Extract tokens from response urls and output a line with each token formatted with outputfmt.

    Args:
        responses:
        outputfmt:

    Returns:
        text (str) with one output line per response

    Examples:
        >>> extract_and_format_tokens([r], "{r.status_code} \t {r.url} \t {jobid} \t {token}")

    """
    if outputfmt.lower() == 'yaml':
        text = responses_to_yaml(responses)
    else:
        tokens = get_tokens(responses)
        jobids = get_jobids(responses)
        text = "\n".join(outputfmt.format(token=token, r=response, jobid=jobid, url=response.url)
                         for token, response, jobid in zip(tokens, responses, jobids))
    return text


def save_tokens(responses, outputfn, outputfmt="{token}", verbose=0):
    """ Save tokens to file. """
    token_formatted_text = extract_and_format_tokens(responses, outputfmt=outputfmt)
    if verbose and verbose > 1:
        print("\nResponse tokens, urls:")
        print(token_formatted_text)
    with open(outputfn, 'w') as fp:
        fp.write(token_formatted_text)


def submit_nupack_partition_jobs(
        seq_batches, job_param,
        seq_batch_is_design_output=False,
        session=None, sleep=2,
        savetokenstofile=None,
        tokenoutputfmt="yaml",
        open_webbrowser=True,
        print_jobparams=False,  # print parameters for each submitted job
        verbose=None,
):
    """Submit NuPack partition analysis batch job(s).

    Args:
        seq_batches: Either (a) a list of batches, each batch a list of sequence dicts,
                     or (b) a file with sequence batch information to be parsed by parse_sequence_batch_file().
        job_param: A dict with job parameters (e.g. 'temperature', 'na_salt', etc).
        session: A requests Session object to use. A new session is created if None is provided.
        sleep: The time, in seconds, to sleep between submitting each batch job to NuPack web service.
        savetokenstofile: Save NuPack tokens to this file.
        tokenoutputfmt: How to format each token when writing it to file, e.g. if you want to add url info, etc.
        open_webbrowser: If True, the response url is opened in the system-default web browser.
        print_jobparams: If True, print information about each submitted job to stdout.

    Returns:
        A list of response objects, one for each submitted job.

    """

    if isinstance(seq_batches, str):
        seqs_batchfile = seq_batches
        if seq_batch_is_design_output:
            # returns a single batch/list of sequences
            seq_batches = [seq_batch_from_design_output_file(seqs_batchfile)]
        else:
            seq_batches = parse_sequence_batch_file(seqs_batchfile)
    else:
        seqs_batchfile = None

    if session is None:
        session = requests.Session()
    n_jobs = len(seq_batches)
    responses = []

    if print_jobparams:
        print("General job parameters for all batches:")
        print(yaml.dump(job_param, default_flow_style=False))

        if verbose and verbose > 1:
            print("\nSequence batches:")
            pprint(seq_batches)

    for i, seq_batch in enumerate(seq_batches, 1):
        print("\n\nProccessing sequence batch {} of {}".format(i, n_jobs))
        if print_jobparams:
            print("Sequence batch parameters:")
            print(yaml.dump(seq_batch, default_flow_style=False))
        if len(seq_batch) == 0:
            # guard against empty batches:
            print("WARNING, batch {} of {} is empty, {!r} - skipping...".format(i, n_jobs, seq_batch))
        if not len(seq_batch) == int(job_param["num_sequences"]):
            print("Adjusting num_sequences to:", len(seq_batch))
            job_param["num_sequences"] = str(len(seq_batch))
        print("Dispatching batch {} of {}...".format(i, n_jobs))
        r = dispatch(job_param, seq_batch, session=session, verbose=verbose)
        time.sleep(sleep)
        print("Got response: {} - History: {} - URL: {}".format(r, r.history, r.url))
        # History is typically a single HTTP 302 Redirection/Found response
        # The last 200 response is a "job processing" page (nupack.org/partition/show/1144222?token=l6tOAGJdyV)
        # When the job has completed, the URL will return a HTTP 302 response, redirecting to the results page,
        # e.g. http://nupack.org/partition/histogram_detail/1144222?token=l6tOAGJdyV&strand_id=0
        # The full job can then be downloaded from http://nupack.org/partition/download_tar/1144209?token=txcIeEalxH
        responses.append(r)
        if open_webbrowser:
            webbrowser.open(r.url)

    if savetokenstofile:
        if isinstance(savetokenstofile, str):
            outputfn = savetokenstofile.format(date=datetime.now(), batch=seqs_batchfile)
        else:
            if not isinstance(seqs_batchfile, str):
                print(
                    "\nWARNING: COULD NOT WRITE TOKENS TO FILE."
                    "IN ORDER TO SAVE TO FILE, EITHER `savetofile` OR `seqs_batches` MUST BE A FILENAME/FORMAT.")
                outputfn = None
                token_formatted_text = extract_and_format_tokens(responses, outputfmt=tokenoutputfmt)
                print(token_formatted_text)
            else:
                outputfn = seqs_batchfile + '.tokens.txt'
        if outputfn:
            save_tokens(responses, outputfn, tokenoutputfmt, verbose=verbose)
            print("\nTokens saved to file:", outputfn)

    return responses


def main(argv=None):
    """Main driver, executed when running this module as a script.

    Parse command line args and pass them to submit_nupack_partition_jobs().

    """
    argns, _ = parse_args(argv)

    # global verbose
    verbose = argns.verbose or 0  # Is None if not provided, not 0.

    job_param, def_seq_param = get_defaults()
    if argns.jobparams:
        job_param.update(load_yaml(argns.jobparams))
    session = requests.Session()

    responses = submit_nupack_partition_jobs(
        seq_batches=argns.batch,
        job_param=job_param,
        seq_batch_is_design_output=argns.seq_batch_is_design_output,
        session=session,
        sleep=2,
        savetokenstofile=argns.savetokens,
        tokenoutputfmt=argns.outputfmt,
        open_webbrowser=argns.browser,
        print_jobparams=argns.print_jobparams,
        verbose=verbose
    )

    print("\nDONE!")
    return responses


def parse_args(argv):
    """Parse command line arguments.
    """

    # Use ArgumentDefaultsHelpFormatter formatter class to display default argument values when printing help.
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)


    # "{}:{} {}"
    # parser.add_argument('--printfmt', default="{filepath}:{lineno} {line}",
    #                    help="Default format string for printing matches. "\
    #                         "Valid fields are filepath, lineno, line, and row. "\
    #                         "Default is {filepath}:{lineno} {line}. "
    #                         "Inspiration: {filepath: <40}: {row[Sequence Name]: >20} {row[seq]}")

    parser.add_argument('--verbose', '-v', action="count", help="Increase verbosity.")

    # Actually, this seems familiar. I think I made a grep script once which used --criteria <field> <operator> <value>
    # e.g. --criteria conc lt 100  # where lt is "less than".
    parser.add_argument('--sep', metavar="SEPCHAR", help=(
        "Field separator, character separating fields on each line in the sequence_batch file. "
        "`None` will split on all whitespace characters."))
    parser.add_argument('--sleep', metavar="SECONDS", type=int, default=2,
                        help="Wait this number of seconds between each request.")
    parser.add_argument('--no-browser', action="store_false", dest='browser',
                        help="Do not open NuPack job page in browser for every batch request.")
    parser.add_argument('--browser', action="store_true",
                        help="Open NuPack job page in browser for every batch request.")
    parser.add_argument('--print-jobparams', action="store_true",
                        help="Print all job parameters (both general and for each sequence batch).")

    # OBS: ArgParse uses %-formatting so you need to escape '%' in help strings.
    parser.add_argument(
        '--savetokens', metavar="TOKENSOUTPUT.txt",
        # default="{batch}.{date:%Y%m%d-%H%M}.nupack-job-tokens.txt",
        default="{batch}.{date:%Y%m%d-%H%M}.nupack-jobs.yaml",
        help=(
            "Save tokens and urls to this file (using outputfmt). "
            "Format placeholders include `batch` and `date`, e.g. {date:%%Y%%m%%d-%%H%%M} and {batch}"))
    parser.add_argument(
        '--outputfmt', metavar="TOKEN_OUTPUT_LINE_FORMAT",
        # default="{token}, {r.url}",
        default="YAML",
        help=(
            "Save token and url for every batch job using this format. "
            "{r} is response and {token} is token. "
            "NEW: --outputfmt YAML will convert all batch responses to yaml."
    ))
    parser.add_argument('--jobparams', metavar="JOBPARAMS.yaml", help=(
        "YAML-formatted file with a dict specifying common job parameters (e.g. `temperature`, `na_salt`, etc. "
        "Full list of job parameters: "
        # Need the '+' to separate, otherwise the strings are concatenated before the .join()
        + ", ".join(sorted(default_partition_job_params.keys()))
    ))

    parser.add_argument('--seq-batch-is-design-output', action="store_true", help=(
        "Treat sequence batch file as output from NuPack's `tubedesign` command, "
        "and analyze the strands found therein."
    ))
    parser.add_argument('batch', metavar="SEQUENCES_BATCHES_FILENAME", help=(
        "Load sequence batches from this file, "
        "and submit each one for nupack.org partition analysis. "
        "The batches are separated by an empty line (\\n\\n). "
        "Each batch consists of one or more lines, one line per sequence/specie. "
        "The parameter on the sequence line is separated by a whitespace (can be changed with --sep), "
        "in the order: Name, Sequence, Concentration, Scale "
        "Where Name is name of the specie, Sequence is the sequence/content, "
        "Concentration is a numeric value, and scale is the molar magnitude, "
        "e.g. -6 for uM, -9 for nM and so forth."))
    # NOTE: Windows does not support wildcard expansion in the default command line prompt!
    # parser.add_argument('files', nargs='*', help="")

    return parser.parse_args(argv), parser


if __name__ == '__main__':
    main()

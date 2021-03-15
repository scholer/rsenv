# Copyright 2018-2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>

"""

OBS: generic_text_extractor_cli is basically just `grep`,
but it has support for a settings file where I can save the regex locally in this directory.

This is part of an alternative solution to the "idt_download_especs" scripts.

Instead of doing everything at once, we split the process up into two more generic approaches:

1. First, extract the needed values from a text file, e.g. order numbers in HTML copy/pasted from the orderstatus page.
    Save the extracted values in a text file, e.g. `extracted_values.txt`.
    Extraction settings are saved in a generic yaml file, e.g. `generic_text_extractor.yaml`

2. Then, for each extracted value, interpolate with a given url format string, and download.
    Settings are saved in a generic yaml file, e.g. `generic_batch_downloader.yaml`
    Settings include e.g. cookies for authentication.


"""

import sys
import os
import pathlib
import re
import yaml
import click
from pprint import pprint


@click.command()
@click.option('--settings-file', default='generic_text_extractor.yaml')
@click.option('--output-file')
@click.option('--extract-regex')
@click.option('--verbose', count=True)
@click.argument('input-files', nargs=-1)
def generic_text_extractor_cli(
        input_files,
        settings_file='generic_text_extractor.yaml',
        output_file=None,  # Default '-' set later
        extract_regex=None,
        output_line_format=None,
        verbose=None,
):
    """ Generic text extractor CLI.

    Args:
        input_files: A list with one or more filenames for input files to read and extract text from.
        settings_file: A YAML file containing parameters. You can place `extract_regex` in here, if you want.
        output_file: Write the extracted values to this output file.
        extract_regex: Specify the extraction regex directly from the command line.
            Alternatively, you can specify the extract_regex in the settings file.
        output_line_format: How to write each match (group).
        verbose: Increase verbosity to print more information during execution (printed to stderr).

    Returns:
        A list of matches.

    Usage:
        1. Place the text you want to extract values from in a file, e.g. `inputfile.html`.
        2. Specify the extraction regex pattern, either on the command line, or in a settings file,
            e.g. `generic_text_extractor.yaml`
        3. Run `generic-text-extractor`, passing the inputfile and extract-regex/settings file as arguments.

    Examples:



    Notes:

        * A good way to test/develop your regex patterns is using an interactive regex tester,
            e.g. pythex.org, regextester.com, or regex101.com.

    """

    try:
        with open(settings_file) as fp:
            config = yaml.load(fp)
    except FileNotFoundError:
        print("No settings file '%s' found, using empty config." % (settings_file,), file=sys.stderr)
        config = {}
    if verbose is None:
        verbose = config.get('verbose', 0)
    if verbose > 1:
        print("config:", file=sys.stderr)
        pprint(config, stream=sys.stderr)
    if extract_regex is None:
        extract_regex = config['extract_regex']
    if 'input_files' in config and config['input_files']:
        input_files = list(input_files)  # Input might be a tuple.
        input_files.extend(config['input_files'])
    if output_file is None:
        output_file = config.get('output_file', '-')
    if output_line_format is None:
        output_line_format = config.get('output_line_format', "{}")
    if verbose:
        print(f"extract_regex: {extract_regex}")
        print(f"input_files: {input_files}")
        print("output_file: %s" % (output_file,), file=sys.stderr)
        print("output_line_format: %s" % (output_line_format,), file=sys.stderr)

    close_file = False
    if output_file == '-':
        output_file = sys.stdout
    elif isinstance(output_file, (str, pathlib.Path)):
        output_file = open(output_file, 'w', encoding='utf8')
        close_file = True
    else:
        print("output_file is: %r - assuming it is a writable file object..." % (output_file,), file=sys.stderr)

    all_matches = []
    for input_file in input_files:
        if isinstance(extract_regex, str):
            extract_regex = re.compile(extract_regex)  # , flags=re.MULTILINE+re.)
        input_text = open(input_file, encoding='utf8').read()
        # findall() returns list of matching text, or list of tuples if pattern has multiple capture groups.
        # finditer() returns re.match objects - this is often a better, more consistent solution.
        matches = extract_regex.findall(input_text)
        all_matches.extend(matches)
        print("%s matches found in file %s (regex=%s)" %
              (len(matches), input_file, extract_regex.pattern), file=sys.stderr)

        if output_file:
            for matched_text in matches:
                # The returned results of re.findall() changes depending on whether
                # the regex pattern has zero, one, or multiple capturing groups!
                # If the regex has zero or one capturing group, then findall() returns a list of strings.
                # If the regex has multiple capturing groups, then findall() returns a list of tuples.
                # In order for this to work consistently for both cases, convert strings to tuples:
                if isinstance(matched_text, str):
                    matched_text = (matched_text,)
                if verbose:
                    print("matched_text:", matched_text, file=sys.stderr)
                print(output_line_format.format(*matched_text), file=output_file)
            print("%s matches printed to file: %s" % (len(matches), output_file.name), file=sys.stderr)
    if close_file:
        output_file.close()

    return all_matches


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
@click.argument('input-files', nargs=-1)
def generic_text_extractor_cli(
        input_files,
        settings_file='generic_text_extractor.yaml',
        output_file=None,  # Default '-' set later
        extract_regex=None,
        output_line_format=None,
):
    """ Generic text extractor CLI.

    Args:
        input_files: A list with one or more filenames for input files to read and extract text from.
        settings_file: A YAML file containing parameters. You can place `extract_regex` in here, if you want.
        output_file: Write the extracted values to this output file.
        extract_regex: Specify the extraction regex directly from the command line.
            Alternatively, you can specify the extract_regex in the settings file.
        output_line_format: How to write each match (group).

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
        print("No settings file '%s' found, using empty config." % (settings_file,))
        config = {}
    print("config:", file=sys.stderr)
    pprint(config, stream=sys.stderr)
    if extract_regex is None:
        extract_regex = config['extract_regex']
    if 'input_files' in config and config['input_files']:
        input_files = list(input_files)  # Input might be a tuple.
        input_files.extend(config['input_files'])
    if output_file is None:
        output_file = config.get('output_file', '-')
    print("output_file: %s" % (output_file,), file=sys.stderr)
    if output_line_format is None:
        output_line_format = config.get('output_line_format', "{}")
    print("output_line_format: %s" % (output_line_format,), file=sys.stderr)

    for input_file in input_files:
        if isinstance(extract_regex, str):
            extract_regex = re.compile(extract_regex)  # , flags=re.MULTILINE+re.)
        input_text = open(input_file, encoding='utf8').read()
        # findall() returns matching text, finditer() returns re.match objects.
        matches = extract_regex.findall(input_text)
        print("%s matches found in file %s (regex=%s)" %
              (len(matches), input_file, extract_regex.pattern), file=sys.stderr)
        close_file = False
        if output_file == '-':
            output_file = sys.stdout
        elif isinstance(output_file, (str, pathlib.Path)):
            output_file = open(output_file, 'w', encoding='utf8')
            close_file = True
        else:
            print("output_file is: %r - assuming it is a writable file object..." % (output_file,), file=sys.stderr)

        if output_file:
            for matched_text in matches:
                # print(matched_text)
                print(output_line_format.format(*matched_text), file=output_file)
            print("%s matches printed to file: %s" % (len(matches), output_file.name), file=sys.stderr)
        if close_file:
            output_file.close()

        return matches


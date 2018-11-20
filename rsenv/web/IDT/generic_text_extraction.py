# Copyright 2018 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>

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
    Settings include e.g. IDT cookies.


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
@click.option('--output-file', default='-')
@click.option('--extract-regex')
@click.argument('input-files', nargs=-1)
def generic_text_extractor_cli(
        input_files,
        settings_file='generic_text_extractor.yaml',
        output_file='-',
        extract_regex=None,
):

    with open(settings_file) as fp:
        config = yaml.load(fp)
    print("config:", file=sys.stderr)
    pprint(config, stream=sys.stderr)
    if extract_regex is None:
        extract_regex = config['extract_regex']
    if 'input_files' in config and config['input_files']:
        input_files.extend(config['input_files'])

    for input_file in input_files:
        if isinstance(extract_regex, str):
            extract_regex = re.compile(extract_regex)  # , flags=re.MULTILINE+re.)
        input_text = open(input_file).read()
        # findall() returns matching text, finditer() returns re.match objects.
        matches = extract_regex.findall(input_text)
        print("%s matches found in file %s (regex=%s)" %
              (len(matches), input_file, extract_regex.pattern), file=sys.stderr)
        close_file = False
        if output_file == '-':
            output_file = sys.stdout
        elif isinstance(output_file, (str, pathlib.Path)):
            output_file = open(output_file, 'w')
            close_file = True

        if output_file:
            for matched_text in matches:
                print(matched_text)
        if close_file:
            output_file.close()

        return matches


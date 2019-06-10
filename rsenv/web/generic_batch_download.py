# Copyright 2018-2019 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>

"""

This is an alternative to the "idt_download_especs" scripts.

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
import requests
import click
from pprint import pprint


def load_txt(input_file, line_comment_char='#', val_sep=None):
    with open(input_file, encoding='utf8') as fp:
        lines = fp.readlines()
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line and line[0] != line_comment_char]
    if val_sep:
        lines = [line.split(val_sep) for line in lines]
    return lines


@click.command()
@click.option('--settings-file', default='generic_batch_downloader.yaml')
@click.option('--string-format-method')
@click.option('--download-url-format')
@click.option('--output-dir', default='.')
@click.option('--filename-format')
@click.option('--overwrite/--no-overwrite', default=False)
@click.option('--line-comment-char')
@click.option('--value-separator')
@click.argument('input-files', nargs=-1)
def generic_batch_downloader_cli(
        input_files,
        input_file_format=None,
        settings_file='generic_batch_downloader.yaml',
        output_dir='.',
        download_url_format=None,
        filename_format=None,
        overwrite=False,
        string_format_method=None,
        line_comment_char=None,
        value_separator=None,
        ignore_http_errors=False,
):
    """ Generic batch downloader CLI.

    Args:
        input_files:
        input_file_format: Not currently used, but may eventually be used to support other input file formats,
            e.g. csv.
        settings_file: Load default settings from this file. Arguments specified on the command line takes preference.
        output_dir: Save downloaded files to this directory.
        download_url_format: How to format the download URLs based on the values read from input files. Required.
        filename_format: How to format the downloaded files. Required.
        overwrite: If True, overwrite existing files. If False, ignore file and move to next download.
            Useful for interrupted batch downloads.
        string_format_method: Which formatting method to use to format URLs and filenames.
            Valid values include '%' and '{}'.
        line_comment_char: Exclude lines in inputfiles starting with this character. Default: '#'.
        value_separator: If given, split each line from input files into multiple values.
        ignore_http_errors: Set to True to ignore http errors and continue to next file.

    Returns:
        A list of outputfiles with the filenames of the downloaded files.

    Usage:
        1. Generate one or more files with values used for the batch downloader.
            You can use the `generic-text-extractor` CLI if you have e.g. a HTML file that contains download URLs.
        2. Optional: Create a settings file with settings/arguments used for this CLI.
            If you do not use a settings file, you must provide the values as CLI arguments.
            Required arguments include `download_url_format` and `filename_format`.
        3. Run generic-batch-downloader:

    Examples:

        Basic example:
        `generic-batch-downloader --download-url-format "www.example.com/file/%s" --filename-format "%s.csv" input.txt`

        Other examples use default settings file:
            generic-batch-downloader input.txt

        `generic_batch_downloader.yaml` example 1:

            downlaod_url_format: "www.example.com/file/%s"
            filename_format: "%s.csv"

        `generic_batch_downloader.yaml` example 2:

            downlaod_url_format: "www.example.com/file/{0}"
            filename_format: "{1}.csv"
            string_format_method: "{}"
            value_separator_char: "\t"
            overwrite: false
            cookies:
                token: <private-login-token>

    """

    with open(settings_file) as fp:
        config = yaml.load(fp)
    print("config:", file=sys.stderr)
    pprint(config, stream=sys.stderr)
    if download_url_format is None:
        download_url_format = config['download_url_format']
    if filename_format is None:
        filename_format = config['filename_format']
    if value_separator is None:
        value_separator = config.get('value_separator', None)
    if line_comment_char is None:
        line_comment_char = config.get('line_comment_char', "#")
    if string_format_method is None:
        string_format_method = config.get('string_format_method', '{}')

    if 'input_files' in config and config['input_files']:
        input_files = list(input_files)  # Input might be a tuple.
        input_files.extend(config['input_files'])

    session = requests.Session()
    if config.get('cookies'):
        session.cookies.update(config['cookies'])

    outputfiles = []
    for input_file in input_files:
        values = load_txt(input_file, line_comment_char=line_comment_char, val_sep=value_separator)
        n_values = len(values)
        print(f"\nValues from input file '{input_file}':", file=sys.stderr)
        print(values, file=sys.stderr)

        for val_num, value in enumerate(values, 1):
            print(f"\nProcessing value {val_num} of {n_values} from input file {input_file}...")
            if isinstance(value, str):
                if string_format_method == '{}':
                    url = download_url_format.format(value)
                    filename = filename_format.format(value)
                else:
                    url = download_url_format % (value,)
                    filename = filename_format % (value,)
            elif isinstance(value, list):
                if string_format_method == '{}':
                    url = download_url_format.format(*value)
                    filename = filename_format.format(*value)
                else:
                    url = download_url_format % tuple(value)
                    filename = filename_format % tuple(value)
            else:  # assume dict-like objects.
                if string_format_method == '{}':
                    url = download_url_format.format(**value)
                    filename = filename_format.format(**value)
                else:
                    url = download_url_format % value
                    filename = filename_format % value

            if os.path.exists(filename) and not overwrite:
                print(" - OBS: File '%s' already exists, and overwrite is False; skipping this file..." % (filename,))
                continue
            print(" - GET'ing URL:", url)
            res = session.get(url)
            print(" - Response:", res)
            if not ignore_http_errors:
                res.raise_for_status()
            print(" - Saving %s kb to file: %s" % (len(res.content)//1024+1, filename))
            with open(filename, 'wb') as fp:
                fp.write(res.content)
            outputfiles.append(filename)

    return outputfiles

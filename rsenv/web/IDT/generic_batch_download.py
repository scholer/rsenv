# Copyright 2018 Rasmus Scholer Sorensen <rasmusscholer@gmail.com>

"""

This is an alternative to the "idt_download_especs" scripts.

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
import requests
import click
from pprint import pprint


def load_txt(input_file, line_comment_char='#'):
    with open(input_file) as fp:
        lines = fp.readlines()
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line and line[0] != line_comment_char]
    return lines


@click.command()
@click.option('--settings-file', default='generic_batch_downloader.yaml')
@click.option('--string-format-method', default='%')
@click.option('--download-url-format')
@click.option('--output-dir', default='.')
@click.option('--filename-format')
@click.option('--overwrite/--no-overwrite', default=False)
@click.option('--line-comment-char')
@click.argument('input-files', nargs=-1)
def generic_batch_downloader_cli(
        input_files,
        input_file_format=None,
        settings_file='generic_batch_downloader.yaml',
        output_dir='.',
        download_url_format=None,
        filename_format=None,
        overwrite=False,
        string_format_method='%',
        line_comment_char='#',
):

    with open(settings_file) as fp:
        config = yaml.load(fp)
    print("config:", file=sys.stderr)
    pprint(config, stream=sys.stderr)
    if download_url_format is None:
        download_url_format = config['download_url_format']
    if filename_format is None:
        filename_format = config['filename_format']

    if 'input_files' in config and config['input_files']:
        input_files.extend(config['input_files'])

    session = requests.Session()
    if config.get('cookies'):
        session.cookies.update(config['cookies'])

    for input_file in input_files:
        values = load_txt(input_file, line_comment_char=line_comment_char)
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
            else:
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
            res.raise_for_status()
            print(" - Saving %s kb to file: %s" % (len(res.content)//1024+1, filename))
            with open(filename, 'wb') as fp:
                fp.write(res.content)



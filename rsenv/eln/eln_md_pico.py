# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

"""

Module for dealing with Electronic laboratory notebook journals in Pico Markdown format,
as used with e.g. the Nextcloud Pico_CMS app.

Pico Markdown documents are generally just markdown documents with a standard "YAML front matter" (YFM) header,
separated by the main document with "---" on a single, separate line (also indicates "end of document" in YAML).

Pico Markdown documents supports %variable_placeholders%, e.g. %meta.title%, where meta is the YFM header.

"""

import os
import glob
import yaml
import yaml.scanner
import pandas as pd
import click
import inspect

from rsenv.fileutils.fileutils import find_files

WARN_MISSING_YFM = False
WARN_YAML_SCANNER_ERROR = True

REQUIRED_PICO_KEYS = ('title', 'description', 'author', )
REQUIRED_EXP_KEYS = ('expid', 'titledesc', 'status', 'startdate', 'enddate', 'result')
REQUIRED_KEYS = REQUIRED_PICO_KEYS + REQUIRED_EXP_KEYS


def find_md_files(basedir='.', pattern=r'*.md', pattern_type='glob'):
    # return list(find_files(start_points=[basedir], include_patterns=[pattern]))
    # Alternative, using glob:
    return glob.glob(os.path.join(basedir, '**/*.md'))


def get_journals(basedir='.', add_fileinfo_to_meta=True, exclude_if_missing_yfm=True):
    files = find_md_files(basedir=basedir)
    # Note: I tried two versions of this, one where I had variables and one where I just had everything directly
    # in the dict, e.g. j['filename']. The dict-only was shorter, but below is cleaner.
    # Above is 359 chars on 11 lines, below is 265 chars on 5 lines. But above is still cleaner.
    journals = []
    for fn in files:
        dirname, basename = os.path.split(fn)
        fileinfo = {
            'filename': fn,
            'dirname': dirname,
            'basename': basename,
        }
        raw_content = open(fn, 'r', encoding='utf-8').read()
        if '\n---\n' in raw_content:
            yfm_content, md_content = raw_content.split('\n---\n', maxsplit=1)
            try:
                yfm = yaml.load(yfm_content)
                if add_fileinfo_to_meta:
                    yfm.update(fileinfo)
            except yaml.scanner.ScannerError as exc:
                if WARN_YAML_SCANNER_ERROR:
                    print(f"WARNING: ScannerError while parsing YFM of file {fn}.")
                yfm = None
        else:
            if WARN_MISSING_YFM:
                print(f"WARNING: {fn} did not contain any YFM end-of-document separator ('\\n---\\n').")
            yfm = None
        if yfm or not exclude_if_missing_yfm:
            journals.append({
                'filename': fn,
                'fileinfo': fileinfo,
                'raw_content': raw_content,
                'yfm_content': yfm_content,
                'meta': yfm,
            })

    # journals = [{'filename': fn} for fn in files]
    # for j in journals:
    #     j['filedir'] = os.path.dirname(j['filename'])
    #     j['raw_content'] = open(j['filename'], 'r', encoding='utf-8').read()
    #     j['yfm_content'], j['md_content'] = j['raw_content'].split('\n---\n', maxsplit=1)
    #     j['meta'] = yaml.load(j['yfm_content'])
    return journals


def get_journals_metadata(basedir='.', add_fileinfo_to_meta=True, exclude_if_missing_yfm=True):
    journals = get_journals(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=exclude_if_missing_yfm)
    # print("\n".join("{}: {}".format(j['filename'], type(j['meta'])) for j in journals))
    metadata = [journal['meta'] for journal in journals]
    return metadata


def get_started_exps(basedir='.', add_fileinfo_to_meta=True):
    all_meta = get_journals_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [m for m in all_meta if m['status'] == 'started']
    return started


def get_unfinished_exps(basedir='.', add_fileinfo_to_meta=True):
    """ Journals where either status is not ('completed' or 'cancelled') or 'complete' but enddate is None.
    Edit: This is just where enddate is None and 'status' is not 'cancelled'.
    """
    all_meta = get_journals_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [
        m for m in all_meta
        # if m.get('status') != 'cancelled' and (m.get('status') != 'completed' and m.get('enddate') is not None)
        # if not (m.get('status') == 'cancelled' or (m.get('status') == 'completed' and m.get('enddate') is not None))
        if m.get('enddate') is None and m.get('status') != 'cancelled'
    ]
    return started


def print_started_exps(basedir='.', rowfmt="{expid:<10} {titledesc}"):
    started = get_started_exps(basedir=basedir)
    print("\n".join(rowfmt.format(**meta) for meta in started))


def print_unfinished_exps(basedir='.', rowfmt="{expid:<10} {titledesc}", print_header=True):
    unfinished = get_unfinished_exps(basedir=basedir)
    # print("\n".join(rowfmt.format(**meta) for meta in unfinished))
    if print_header:
        keys_titlecased = [k.title() for k in REQUIRED_KEYS]
        hdr_str = rowfmt.format(**dict(zip(REQUIRED_KEYS, keys_titlecased)))
        print(hdr_str)
        print("-"*(len(hdr_str)+8*hdr_str.count("\t")))
    for meta in unfinished:
        try:
            print(rowfmt.format(**meta))
        except KeyError as exc:
            print("{}: {}, for file {} - keys: {}".format(exc.__class__.__name__, exc, meta['filename'], meta.keys()))


def print_journal_yfm_issues(
        basedir='.',
        required_keys=REQUIRED_KEYS,
):
    required_keys = set(required_keys)
    journals = get_journals_metadata(basedir=basedir, add_fileinfo_to_meta=True)
    for meta in journals:
        missing = required_keys.difference(meta.keys())
        if missing:
            print("FILE:", meta['filename'])
            print(" - MISSING KEYS:", missing)


# Pandas DataFrame versions of the functions above (if you prefer the convenience of DataFrames):

def get_journals_metadata_df(basedir='.', add_fileinfo_to_meta=True):
    metadata = get_journals_metadata(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = pd.DataFrame(metadata)
    return df


def get_started_exps_df(basedir='.', add_fileinfo_to_meta=True):
    df = get_journals_metadata_df(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = df.loc[df['status'] == 'started', :]
    return df


def print_started_exps_df(basedir='.', cols=('expid', 'titledesc')):
    df = get_started_exps_df(basedir=basedir)
    print(df.loc[:, cols])


print_started_exps_cli = click.Command(
    callback=print_started_exps,
    name=print_started_exps.__name__,
    help=inspect.getdoc(print_started_exps),
    params=[
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc}'),  # remember: param_decls is a list, *decls.
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_unfinished_exps_cli = click.Command(
    callback=print_unfinished_exps,
    name=print_unfinished_exps.__name__,
    help=inspect.getdoc(print_unfinished_exps),
    params=[
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc:<40}  [enddate: {enddate}]'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])


print_journal_yfm_issues_cli = click.Command(
    callback=print_journal_yfm_issues,
    name=print_journal_yfm_issues.__name__,
    help=inspect.getdoc(print_journal_yfm_issues),
    params=[
        # click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc} (enddate={enddate})'),
        click.Argument(
            ['basedir'], default='.', nargs=1, type=click.Path(dir_okay=True, file_okay=False, exists=True))
])

if __name__ == '__main__':
    # print_started_exps_cli()
    # print_unfinished_exps_cli()
    print_journal_yfm_issues_cli()

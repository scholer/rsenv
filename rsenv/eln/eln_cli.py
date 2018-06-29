import inspect

import click

from rsenv.eln.eln_md_pico import load_all_documents_metadata, REQUIRED_KEYS


def get_started_exps(basedir='.', add_fileinfo_to_meta=True):
    """ Get metadata for journals with status='started'. """
    all_meta = load_all_documents_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [m for m in all_meta if m['status'] == 'started']
    return started


def get_unfinished_exps(basedir='.', add_fileinfo_to_meta=True):
    """ Journals where either status is not ('completed' or 'cancelled') or 'complete' but enddate is None.
    Edit: This is just where enddate is None and 'status' is not 'cancelled'.
    """
    all_meta = load_all_documents_metadata(
        basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta, exclude_if_missing_yfm=True)
    started = [
        m for m in all_meta
        # if m.get('status') != 'cancelled' and (m.get('status') != 'completed' and m.get('enddate') is not None)
        # if not (m.get('status') == 'cancelled' or (m.get('status') == 'completed' and m.get('enddate') is not None))
        if m.get('enddate') is None and m.get('status') != 'cancelled'
    ]
    return started


def print_started_exps(basedir='.', rowfmt="{expid:<10} {titledesc}"):
    """ Print journals with status='started'. """
    started = get_started_exps(basedir=basedir)
    print("\n".join(rowfmt.format(**meta) for meta in started))


def print_unfinished_exps(basedir='.', rowfmt="{expid:<10} {titledesc}", print_header=True):
    """ Print journals with status not 'completed'. """
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
    """ Print journals that have YFM issues, e.g. missing YFM keys. """
    required_keys = set(required_keys)
    journals = load_all_documents_metadata(basedir=basedir, add_fileinfo_to_meta=True)
    for meta in journals:
        missing = required_keys.difference(meta.keys())
        if missing:
            print("FILE:", meta['filename'])
            print(" - MISSING KEYS:", missing)




print_started_exps_cli = click.Command(
    callback=print_started_exps,
    name=print_started_exps.__name__,
    help=inspect.getdoc(print_started_exps),
    params=[
        # remember: param_decls is a list, *decls.
        click.Option(['--rowfmt'], default='{status:^10}: {expid:<10} {titledesc}'),
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

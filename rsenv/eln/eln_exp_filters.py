# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

from zepto_eln.md_utils.document_io import load_all_documents_metadata

from rsenv.eln.eln_md_pico import REQUIRED_KEYS


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

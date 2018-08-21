# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

from zepto_eln.md_utils.document_io import load_all_documents_metadata

from rsenv.eln.eln_md_pico import REQUIRED_KEYS


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
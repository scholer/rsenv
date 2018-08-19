# Copyright 2018 Rasmus Scholer Sorensen, <rasmusscholer@gmail.com>

import pandas as pd

from rsenv.eln.eln_md_pico import load_all_documents_metadata



# Pandas DataFrame versions of the functions above (if you prefer the convenience of DataFrames):

def get_journals_metadata_df(basedir='.', add_fileinfo_to_meta=True):
    """ Get journal metadata as a Pandas DataFrame. """
    metadata = load_all_documents_metadata(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = pd.DataFrame(metadata)
    return df


def get_started_exps_df(basedir='.', add_fileinfo_to_meta=True):
    """ Get metadata DataFrame with journals where status='started'. """
    df = get_journals_metadata_df(basedir=basedir, add_fileinfo_to_meta=add_fileinfo_to_meta)
    df = df.loc[df['status'] == 'started', :]
    return df


def print_started_exps_df(basedir='.', cols=('expid', 'titledesc')):
    """ Print metadata DataFrame with journals where status='started'. """
    df = get_started_exps_df(basedir=basedir)
    print(df.loc[:, cols])